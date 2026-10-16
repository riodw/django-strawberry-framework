# Bug hunt 0.0.15 (2): to-do list

Every finding from the 0.0.15 hunt in the t3 worktree (never merged), plus bugs found while fixing them.
Each one is verified on main, fixed at the root, checked by a second agent, landed, then deleted from t3.

Progress: 141 done, 111 to do.

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
- [x] 20. Filter and order set robustness rows (not defects: application Python, no wire input). The `Meta.fields` shape
  gate let a value whose `__class__` raises escape raw on both families (fixed with item 23). The rest need no code: the
  set-class, owner and Filter-class name reads are message labels (item 26's question), and a hostile `__eq__` / `__ne__`
  on `Meta.fields` or a raising `__bool__` owner in `resolve_lazy_class` meets no contract row (django-filter and
  django-graphene-filters read them the same way)
- [x] 21. `list_field.py` and `routers.py` robustness rows (not defects: application Python, no wire input). A field target
  whose `__class__` raised or claimed `type`, or whose registry lookup or replaced definition raised, escaped
  `_validate_djangotype_target` raw on all four field factories against its docstring and spec-020 Decision 5; a factory
  return whose `__class__` raised escaped `_factory_application` raw against spec-046 Decision 11. The class test now asks
  the real type (`is_class`), both definition reads sit inside the contained read with `origin` read only off the
  registry's own definition, and the coroutine test is a guarded `isinstance` (a lazy-proxied coroutine is still closed)
- [x] 22. `types/` robustness rows (not defects: application Python and settings, no wire input). A `Meta` value or entry
  whose `__class__` raised or claimed a type (`model`, `name`, `description`, `primary`, `connection`, `cursor_field`,
  `relation_shapes`, `globalid_strategy` and `RELAY_GLOBALID_STRATEGY`, `interfaces`, `fields` / `exclude` and the other
  field sequences, `optimizer_hints`), a class attribute shadowing a model field, a non-string annotation key whose
  `__repr__` raised, and a `resolve_id_attr` result that is not really a string escaped raw against the GLOSSARY /
  docstring typed-error promises. Each gate is now a guarded `isinstance` (lazy proxies still pass), `Meta.name` /
  `Meta.description` and annotation keys ask the real type, keys render through the guarded repr, and the
  `resolve_id_attr` result is normalized inside its fail-closed guard. Labels, hostile iteration, `__mro__` reads and
  hostile `str`-subclass methods need no code (no contract row)
- [x] 23. `utils/` robustness rows (not defects: application Python and settings, no wire input). A `Meta.fields` whose
  `__class__` raised now gets the typed re-readable rejection on both set families (`canonicalize_set_meta_fields`,
  `FilterSet.get_fields`, `is_re_readable_field_declaration`); `normalize_field_name_sequence`,
  `filter_input_type` / `order_input_type`, the string helpers, `session_store_class`, `resolve_policy`,
  `validated_field_directives`, the `ValidationError` mapper, the input-walk field name and depth label, and the SQL
  statement classifier now keep their documented typed outcome for a value whose `__class__` raises or claims `str`. The
  dynamic-set-class rows were stale (code deleted in `899cb35b`); the `__name__` labels in `utils/inputs.py`,
  `querysets.py` and `write_transaction.py` and the depth-cap knob reads need no code (no contract row)
- [x] 24. Trailing-comma lint rows: t3-only (both were in t3's own hunks); `scripts/check_trailing_commas.py --check` passes on
  main
- [x] 25. Stale test-fixture row: already fixed on main (`a01a2ab8` gave the proxy-target fixtures a private `Meta.apps`)
- [x] 27. Unfiled robustness leads: the `str(key)` and `save()` repr leads were item 19's; the annotation-key, cursor-field,
  adjacent-gate and `__mro__` leads were item 22's; the `Meta.fields` liar was item 23's; the cross-model unwired subclass
  is item 73's question. The relay-seam `__mro__`, `resolve_lazy_class` `__module__` and the orders-skip-unknown-key
  divergence need no code (no contract row; hand-built input only for the last)
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
  (`f.0.0` under `ListField(child=ListField(child=ChoiceField))`, `f.1` under `ListField(child=MultipleChoiceField)`),
  declared over any column they are refused at build, and neither graphene-django nor strawberry-django types nested choice
  lists as enums; no code. Found probing it: items 151-154
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
- [x] 64. Not a defect at HEAD (every malformed offset cursor answered the cursor error), but the decoder's `isascii` term
  was load-bearing, not redundant: `str.isdigit` admits 128 digits `int()` raises on (U+00B2), which without it escaped as a
  masked error on every entry point and past the planner's `PaginationArgumentError`-only catch, and no test failed. The
  decoder now matches the index against `0|[1-9][0-9]*` in full (same accepted set); live rows pin the superscript and the
  mixed non-ASCII digit on the root, and every malformed cursor on the planned nested `booksConnection` window (the nested
  field's `errors[].path`, no window statement)
- [x] 66. The composite-index advisory recommended child-table indexes on columns the child's table does not hold: an MTI
  child declaring its own FK or generic link and ordered by an inherited column (explicit order, `Meta.ordering`,
  `Meta.cursor_field`) was told to add `(holder_id, name, ptr)`, which Django refuses (models.E016), and a generic link whose
  content type sits on the parent got `content_type_id` named on the child. The advisory now resolves every column it names
  as the window does (`Query.resolve_ref`, the query's base table only) and stays silent when any lives off the child's
  table; `pk` orders and spans Django trims to a local column now advise, and an MTI `id` names the parent-link column;
  CHANGELOG item 233; filed 234, 235
- [x] 67. A Django `ValidationError` names no model and no nested item, so a save-time error about a child or related row
  was re-keyed through the backing model's map (a child's `name` landing on the root's renamed `title`, on every flavor)
  while the README, spec-036, spec-039 and the GLOSSARY promised the input the client sent at every depth. The docs now state
  the backing-model reading and the route for failing a nested item at save time (DRF `ValidationError` in the nested shape,
  keyed `shelves.<i>.code`, shown by the fakeshop nested-shelves `create()`); the save-time key map is one level (it built an
  unread child map against the root model). No package wire key moves; CHANGELOG item 238
- [x] 70. Robustness, not a defect (no contract row bounds the admission walk's CPU): a shape walk passed over every
  directive of a node at every fragment expansion, though an argument-less one charges nothing, so 500 spreads of a fragment
  carrying 1495 bare directives (3999 tokens, default policy) walked 85 ms before validation and were admitted (1.8 s at 4x
  tokens and selections). A node's directives are now read once and only those carrying arguments are revisited, each
  charging at least one input node (0.6 ms; 2.5 ms at 4x); no verdict changed across 23,650 differential documents; filed
  241
- [x] 188. Re-checked at `8ca6a481`: a nested list whose `get_queryset` returns `union()` / `intersection()` /
  `difference()` no longer raises `NotSupportedError`; the combined result is served as its pk set, optimizer on and off
  (`5c5e32c5`, item 6; `test_combined_visibility_api.py` 199 passed)
- [x] 189. Re-checked at `8ca6a481`: an overlapping declared and generated lookup runs the generated one, two lookups on
  one key both apply, and `{"id": {"gt": 999}}` on a generated-only field filters (`754ed263`, `9f7ea5dd`, item 4)
- [x] 192. Re-checked at `8ca6a481`: an `allow_blank` serializer `ChoiceField` publishes a `BLANK` member that writes `""`
  (`a5dc6ea3`, item 5)
- [x] 195. Re-checked at `8ca6a481`: `test_audit_marks_target_parse_failure_as_incomplete` and the three `async_executor`
  rows in `tests/utils/test_querysets.py` pass; no fix commit identified (possibly stale when filed)
- [x] 92. A Django `ValidationError` raised at save time (a consumer `Model.save()` / `delete()`, a save / delete /
  `m2m_changed` signal, `ModelForm.save()`, `perform_mutate`, register's user save) reached the client as a masked
  top-level error on the model, ModelForm, plain-form and register flavors, while the serializer flavor mapped it; every
  flavor now returns the `FieldError` envelope, keyed like `full_clean()` / `form.errors` and rolled back, through one
  catch in `mutations/resolvers.py::save_or_field_errors` (plus the forced-update and delete wrappers), with no new
  savepoint and no query-count change; a `ValueError` still propagates. The kanban example's hand-written mapping is gone;
  CHANGELOG item 232; filed 230, 231
- [x] 97. `isnull` declared on a relation key django-filter's table does not name (a forward `ForeignObject` of any link
  width, its reverse, a `GenericRelation`) raised "unrecognized field type" at class creation (dropped under WARN /
  IGNORE) while a `ForeignKey` built a `BooleanFilter`; `filters/sets.py::FilterSet.filter_for_lookup` now replays
  upstream's isnull branch from the merged `BooleanField` selection for those keys (`_null_test_filter_for_relation`),
  so every relation key's `isNull` is a Boolean null test (carrier columns on the raw path, "no visible related row" on
  a scoped target, as on a `ForeignKey`); the policy table still mirrors django-filter. Live row: fakeshop
  `ShelfLabelFilter` `shelf` through the new `allLibraryShelfLabelsFiltered` root; CHANGELOG item 240; filed 239
- [x] 211. A repo-wide `ruff check --fix .` / `ruff format .` rewrote untracked hunt evidence; `[tool.ruff]` now
  `extend-exclude`s `hunt-ws`, so ruff checks only the tracked tree (git-ignored copies such as `.claude/worktrees/` were
  already skipped); `docs/ruffing.md` "Files ruff skips" says so
- [x] 208. Not synced: the hunt worktree `t3code-1cc21548` and its branch are removed (0 commits ahead of main). The
  whole tree, `hunt-ws/` evidence and untracked records included, is archived in `~/t3code-1cc21548-final-2026-10-15.tgz`,
  its uncommitted diff in `~/t3code-1cc21548-uncommitted-2026-10-15.patch`; the remaining cleanup decisions are item 242
- [x] 209. Moot: the owned-changes ledger belonged to the removed hunt worktree (archived with it, item 208)
- [x] 210. Not taken to main: every robustness row it served is decided on main; the migration survives only in item
  208's archive
- [x] 213. The `filters/` docstrings and comments (`filters/inputs.py` x3, `filters/base.py`, `filters/sets.py`) and the
  `tests/filters/` docstrings that narrated an earlier implementation ("previously", "used to", "the old", "before the
  fix", "pre-gate") state the invariant instead; 25 `test_c4_` / `test_r6_` names lose the review label
- [x] 221. `derive_register_fields` reads `USERNAME_FIELD` and every `REQUIRED_FIELDS` entry as plain text (real-type
  `str` gate, base-slot read and iteration), so no consumer dunder decides the dedup or the protected refusal and the
  derived tuple holds base `str` only; a `REQUIRED_FIELDS` that is not a list or tuple (Django's `auth.E001`) or a
  non-string entry raises `ConfigurationError` naming the model; spec-040 Decision 6 and Test plan say so
- [x] 222. Class membership over class objects is an identity scan wherever a consumer metaclass reaches it:
  `TypeRegistry.register` / `_detach_type_from_model`, `FilterSet._filters_along`, `apply_interfaces`,
  `guard_nested_recursion`, `apply_cascade_permissions`, the auth `permission_classes` conflict key and the
  `GeneratedInputArgumentsFactory` subclassing check; an always-equal or raising metaclass `__eq__` no longer drops a type,
  removes the wrong one, truncates a flat filter path, drops an interface, reports a false cycle, admits a different
  permission set or escapes raw; specs 001, 015, 018, 027, 034, 039 and 040 say so (before Python 3.12 `inspect` still
  compares a class with `type` / `object` by equality when Strawberry reads its signature)
- [x] 244. A lone surrogate in a raw relation id over a text-pk target (`editionId: "\ud800"`, a `boundWith` member) or
  in an update / delete `id` over a text-pk non-Relay primary escaped as the masked "An unexpected error occurred." in the
  model, form and serializer flavors (the text preflight ran on scalar leaves only): `type_check_relation_id` and
  `coerce_lookup_id` now run it on the coerced pk before any query, keyed `editionId`, `boundWith.<i>` or `id`, `invalid`;
  well-formed non-ASCII ids still write; fakeshop gains `Printing.bound_with` and the Printing / Edition write mutations
  that reach it; specs 038 and 039 say so
- [x] 224. A `str`-subclass value (a `StrEnum` member, an honest subclass, one whose `__eq__` lies or raises) is read as
  its text: `DjangoOptimizerExtension(strictness=)` stores the vocabulary's own constant, so a lying `__eq__` no longer
  disarms the N+1 guard and a raising one no longer fails every request; `FilterSet` / `OrderSet` `Meta.fields` (list,
  tuple, set, dict keys and lookup values, `filter_fields`, `"__all__"`, any re-readable collection) and `FilterSet`
  `Meta.exclude` read through `utils/inputs.py::plain_set_meta_fields`, so the field its text spells is filtered,
  ordered or excluded instead of refused with a false message or escaping raw; a plain declaration keeps its identity
  and kind; specs 027 and 028 say so
- [x] 100. A random order on a nested connection's target (`"?"` from a hook or `Meta.ordering`, a `Random()` bare,
  composed, behind an alias / `F` / transform, or read in a `When` condition) went into the optimizer window, which
  evaluates the order up to three times per statement: `"?"` raised a masked "Cannot resolve keyword '?'" at plan time
  (the whole root field lost) and `Random()` served wrong cursors and pageInfo, while the root and the optimizer-off
  path served both; `optimizer/plans.py::has_random_term` now leaves such a relation to the per-parent pipeline
  (strictness-visible, a keyset target keeps its own error and its `cursor_field` window), a condition's string value
  stays a literal; spec-033 lists the arm
- [x] 110. The item-56 alias message labelling an owner `'category_id' (source 'category_id')`: not a defect (cosmetic,
  no contract row): the label comes from `rest_framework/inputs.py::raise_writable_source_ownership_errors` and the
  refusal stays the typed `ConfigurationError`
- [x] 113. The consumer pipeline running before the deadline on a connection: duplicate of 114; `8d4f66bd` documents
  `get_queryset`, `check_*_permission` and consumer `FilterSet` / `OrderSet` running before the deadline as trusted
  application code
- [x] 115. Item 12's hot-path AFTER number and a `check_deadline` early return: not a defect (an unmeasured
  micro-optimization; no contract row, only a budget figure)
- [x] 122. `prove_failability.py`'s shared `pristine/<label-digest>__<path>` name per tree: not a defect: the tree lock
  excludes concurrent runs, so no two runs hold the path at once
- [x] 124. ModelForm: an explicit `null` on a non-required choice field or `CharField` over a non-blank text choice
  column stores `""`: not a defect (upstream-matching): Django's `BaseModelForm._get_validation_exclusions` skips model
  validation of an empty value on a non-required form field, and the write rolls back
- [x] 125. ModelForm: no check that a declared field's kind agrees with its column: not a defect (intended): the
  declared form field is the input type, and a value the column refuses is an ordinary field-keyed form error
- [x] 126. A plain `Form` `ChoiceField` publishing `String`: not a defect (upstream-matching): graphene-django's
  `forms/converter.py::convert_form_field_to_string` registers `forms.ChoiceField`
- [x] 127. Lead: a serializer single `ChoiceField` over an `ArrayField` skipping the column's choice check: not a
  defect: a hand-declared single `ChoiceField` cannot write an array column at all (item 45 holds the save failure)
- [x] 144. `workspace.py gc`'s Postgres `stop_if_idle` racing another flow's database create: not a defect:
  `scripts/workspace.py` makes no cross-flow promise and the next run recreates the database
- [x] 148. `scripts/census_test_models.py::_import_map` folding imports into one flat map: not a defect: a documented
  approximation (`_census_tree` states the flow limit, `FACTORY_BEFORE_REBINDING_SEES_FINAL` pins it) that no gate
  depends on
- [x] 151. A declared choice field over a nested `ArrayField(ArrayField(<choices>))` building: not a defect
  (infeasible): a misconfiguration, since the declared field cannot describe a 2-D column;
  `rest_framework/serializer_converter.py::_model_backed_scalar_annotation` returns the declared enum before the nested
  refusal
- [x] 152. `ListField(child=ChoiceField(allow_null=True))` over an `ArrayField` whose element is NOT NULL storing a
  `null` element: not a defect (intended): the declared `allow_null` is the contract and
  `rest_framework/serializer_converter.py::_reject_choice_values_the_column_does_not_list` leaves `None` to it
- [x] 153. A `get_fields()` / `Meta.extra_kwargs` field read as generated, not consumer-declared: not a defect
  (intended): `rest_framework/serializer_converter.py::_is_consumer_declared` fails closed (every mismatched write is
  refused field-keyed) and declaring the field publishes its own type
- [x] 154. `rest_framework/inputs.py::_fingerprint_converter_extra` missing a nested `ListField` leaf drift: not a
  defect: only a nondeterministic `get_serializer_for_schema()` reaches it and schema construction still fails loud;
  `rest_framework/inputs.py::serializer_schema_fingerprint`'s docstring over-promises with "This captures EVERY axis the
  generated input / SDL / reverse map depends on"
- [x] 156. `CaptureQueriesContext` recording no queries on the async transport: not a defect: Django's
  `CaptureQueriesContext` cannot see the asgiref worker thread's connection, and no async query-count assertion relies
  on it
- [x] 157. A winning consumer `Prefetch` issuing more queries optimizer-on than off: not a defect (intended): spec-035's
  consumer-wins rule (`optimizer/plans.py::diff_plan_for_queryset`); BACKLOG B8 holds the opt-in merge
- [x] 159. A combined default manager left unplanned on the nested-relation path: not a defect: the designed fallback
  (`optimizer/nested_fetch.py` returns `"combined"`, served per parent); such a manager breaks Django's own related
  managers too
- [x] 164. Fakeshop's plain `strawberry.field` QuerySet roots raising `SynchronousOnlyOperation` on `/graphql-async/`:
  duplicate of 53 (a hand-written `@strawberry.field` returning a QuerySet runs synchronously)
- [x] 167. Native `relay.node()` failing on a model-label GlobalID: not a defect (intended): spec-032 Decision 3
  dispatches root node fields through the package decode because native `relay.node()` looks ids up by GraphQL type name
- [x] 168. `types/relay.py::_resolve_id_default` lazy-loading a deferred `NodeID` column: not a defect: only a consumer
  `.only()` defers it, which is application configuration
- [x] 169. `workspace.py release` / `gc` raising `NotADirectoryError` on a regular file at the flow path: not a defect
  (infeasible): only a hand-planted file reaches `scripts/workspace.py::_lock_flow_dir`
- [x] 171. No tool measuring coverage of a diff's changed lines: not a defect (a tooling wish, no broken contract)
- [x] 172. START.md's resource-gate probe: not a defect: `pgrep -fl '[p]ytest|[b]asedpyright'` does not match itself and
  the `memory_pressure` reading works, erring conservative
- [x] 175. spec-050 Decision 9 saying only "a positive offset raises the low mark": not a defect: incomplete, not false
  (row 21, C19, states the high mark)
- [x] 176. Async nested connection under a `DjangoListField` root leaving a coroutine: already fixed: not reproducible
  at `43208c0c` on either schema, optimizer on and off
- [x] 177. The test clients refusing a nested non-dict `Mapping` in `variables`: not a defect (upstream-matching): the
  variables go through `json.dumps`, which refuses it as upstream test clients do
- [x] 179. Test strength (the C31 ledger lock row, the C9 gate's `typing.cast` blind spot, a mocked `fcntl.flock` row):
  not a defect: no contract row; test-quality notes only
- [x] 180. Strictness `"raise"` counting a refused-keyset hook-order cursor as malformed: not a defect (intended): the
  page is correct and `test_hook_order_cursor_on_a_refused_keyset_relation_keeps_its_per_parent_page` pins it
- [x] 182. `scripts/clean_up.py` and the `review_*` generators deleting their folders unlocked: not a defect: each
  folder has one owning script and no concurrent writer is known
- [x] 184. `tests/base/test_conf.py` crashing the coverage tracer on Python 3.14: not a defect: an old CPython patch
  release in the local venv; CI is green
- [x] 191. A malformed relation GlobalID nulling the response after a committed sibling mutation: duplicate of 135 (the
  top-level coercion error decides both)
- [x] 193. Directive argument values, variable-definition directives, untyped-position defaults and a 200 KB literal
  uncharged: already fixed by `0c0537e2` (11 positions probed at `43208c0c`)
- [x] 194. An unreproduced enter-side cancel defect: not a defect: the report names no site; the plausible referent, the
  async mutation window, is `1b6a09b1`
- [x] 212. No static gate for a `TYPE_CHECKING`-only name in an eager annotation: not a defect: the floor run of
  `tests/base/test_init.py` is the documented catch (START.md "Toolchain"), and every such name in a module without
  `from __future__ import annotations` is quoted
- [x] 225. `forms/inputs.py::_form_field_basis` checking identifiers before `Meta.fields` narrowing: not a defect
  (infeasible): it needs a form field named by a non-identifier
- [x] 226. A nested serializer's `.fields` skipping the root field-map checks: not a defect (infeasible): it is DRF's
  `BindingDict`, and a bad value lands as a typed `ConfigurationError`
- [x] 227. `exceptions.py::_safe_predicate(isinstance, ...)` evaluating a lazy `save()` return: already fixed:
  `rest_framework/resolvers.py::_checked_saved_result` reads `issubclass(type(saved), model)` (`5cbe15de`)
- [x] 228. `exceptions.py::_safe_arg_repr` not bounding length: not a defect (infeasible): only a custom `save()`
  returning a huge object reaches it, and the wire sees the masked error
- [x] 230. Lead: a `ValidationError` from login's `user_logged_in` -> `update_last_login` -> `User.save()`: not a
  defect: `auth/mutations.py::_django_http_login_establish` compensates fail-closed and re-raises, as Django's `login()`
  propagates
- [x] 239. Lead (perf): the always-empty first arm of a scoped relation `isNull: true`: not a defect: a redundant arm;
  the result is correct
- [x] 243. Exact-type checks written as tuple membership: not a defect (infeasible): only a metaclass whose `__eq__`
  lies reaches them
- [x] 246. `DjangoType` `Meta` names and vocabulary values keeping the consumer's `str` subclass: not a defect
  (infeasible): `TextChoices`, `(str, Enum)` and `StrEnum` members work; only a lying or raising `__eq__` fails
- [x] 247. `Meta.operation` accepted by frozenset membership: not a defect (infeasible): a `StrEnum` member works; only
  a lying `__eq__` fails
- [x] 248. `permissions.py::apply_cascade_permissions(fields=)` comparing `str`-subclass entries by their own dunders:
  not a defect (infeasible): `StrEnum` entries work, and the argument is trusted application Python
- [x] 250. A set-family `Meta.fields` / `Meta.exclude` whose `__class__` claims `dict`: duplicate of 237: the feasible
  shape, a `SimpleLazyObject` declaration, is 237's regression from `53001bdd`; a crafted `__class__` is infeasible
- [x] 237. A `SimpleLazyObject` `Meta.fields` / `Meta.exclude` raised a raw `TypeError` on both set families: fixed,
  `utils/inputs.py::plain_set_meta_fields` reads a lazy declaration (list, tuple, set, frozenset, dict, lazy lookup list,
  a nested proxy) as the object it stands for, so `FilterSet` and `OrderSet` accept every lazy declaration their
  evaluated twin accepts and django-filter's list/tuple declared-filter allowance answers as for the target; 250 is its
  duplicate

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

## To do: found along the way

- [ ] 101. `manage.py import_spec_terms --check` fails on spec-020's terms CSV on main (seen at `eb30dd7e`); a later run
  reported eight specs failing (020, 027, 028, 032, 036, 037, 043 and one more)
- [ ] 107. A writable primary-key relation (OneToOne `primary_key=True`) in an update input fails at request time
  instead of at class creation (The MTI half is not a defect: an auto-created parent link such as `venue_ptr` is not
  published as a writable input.)
- [ ] 109. `pid = PrimaryKeyRelatedField(source="pk")` over a relation primary key builds and every create raises a masked
  TypeError: `backing_model_field` does not resolve `"pk"`, while `write_source_key` does
- [ ] 111. A GenericForeignKey own-name `PrimaryKeyRelatedField(source="content_object")` raises `AttributeError` in
  `_require_relation_primary` (`related_model` is None) instead of `ConfigurationError`
- [ ] 120. `prove_failability.py` has no SIGTERM / SIGHUP handler: a terminated run leaves its mutation in the tree and
  its `ACTIVE-MUTATION.json` marker; recovery is by hand from `restore_with`
- [ ] 121. A crashed `prove_failability.py` run without `--scratch-root` leaves its marker in its own `failability-*`
  directory, so the next default-mode run is not refused and reads the mutated tree; a `pre_image` or `reverse_patch`
  entry would copy the mutated bytes as pristine
- [ ] 123. BUILD.md "Mechanized: `scripts/prove_failability.py`" says the tool's default scratch is "a bare `/tmp` path";
  it is a fresh `failability-*` directory under `TMPDIR`
- [ ] 132. A `SerializerMutation` whose `Meta.fields` narrowing keeps a relation to a Relay-Node type fails schema build
  (`TypeError: Mutation fields cannot be resolved. '<...>PartialInput'`), create and update, e.g. `Shelf.branch`; a non-Relay
  target builds
- [ ] 133. A `PrimaryKeyRelatedField` to a model whose pk is a `OneToOneField` (`PatronProfile`) is refused at schema build
  ("Unsupported Django field type 'OneToOneField' on PatronProfile.patron"); a FK to such a model cannot be written by a
  serializer mutation (fails loud)
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
- [ ] 145. `workspace.py status` can raise `FileNotFoundError` reading `state.json` while a `gc` removes the flow
- [ ] 146. `workspace.py::item_diff` emits the tracked and staged diff first, then the untracked files: staging an unchanged
  added file moves it into the first group, so the diff order and its seal change and `diff --check` fails after staging
  alone; the diff should be one baseline-versus-content diff independent of the index
- [ ] 147. `scripts/build_kanban_md.py::GlossaryInliner._protected` does not protect URI or email autolinks:
  `Read <https://example.com/?q=DjangoListField>.` gets a glossary link inside the URI autolink, changing its destination
  (`<DjangoListField@example.com>` likewise); a later plain mention must still link (the test's mention must not be
  followed by `.`, which `TERM_BOUNDARY_AFTER` reads as a path character). `09d0caa0` already protects `[...]` groups with
  quoted titles, nested-parenthesis destinations, shortcut references and double-backtick code spans
- [ ] 149. `scripts/count_queries.py` with a `--query` document that lacks the `--operation-name` (an anonymous `query { ... }`,
  or a named document without that name) raises an uncaught `CannotGetOperationTypeError` from `execute_sync` and exits 1,
  the "scales with cardinality" code, instead of printing NOT MEASURED and exiting 2
- [ ] 150. `docs/bug_hunt/pbugs.md`'s Postgres scrutiny line has `DESC` `NULL` placement backwards: SQLite sorts `NULL`s
  last on `DESC` and Postgres first
- [ ] 155. Specs 030, 031 and 032 (lines naming the "uv.lock-resolved" Strawberry) and the spec-030 / spec-032 rationale
  companions name strawberry-graphql 0.324.0; `uv.lock` resolves 0.327.7. Re-check each claim against the locked release
- [ ] 158. Outside QUERY operations (operation gate closed: mutation, subscription, a mutation's post-write re-fetch) a planned
  child keeps the hook's consumer `.only()` and gains no link columns, so selected columns lazy-load row by row (fails on
  async); read from code, not reproduced, unreachable from fakeshop
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
- [ ] 165. Item 12's deadline checks fail forward-FK and one-to-one hops inside a mutation payload (rolling back a write that
  used to commit) and error subscription frames past the budget; spec-047 Decision 9 states both (`8d4f66bd`) but no test
  pins either; the async deadline rows also cannot tell a head check from a check inside the `sync_to_async` closure
- [ ] 166. Fixture gap: the async many-side tests miss a broken prefetch-cache lookup in
  `types/resolvers.py::many_resolver` (gaps (b)-(d) are optional fixture work, not defects: the
  reverse many-to-many without `related_name`, the window resolver-key collision (pinned by a two-root-field row) and
  the C11 hook-order rows (on a test-local schema))
- [ ] 170. No test runs `workspace.py prove` (`scripts/workspace.py::_cmd_prove`); its flow lease and copy lock are pinned only
  through `execute`; add a `main(["prove", ...])` row and a two-run contention row
- [ ] 173. The KANBAN "Before a release" checklist (BoardDoc 11) runs `ruff format .` before `ruff check --fix .`, the reverse
  of AGENTS and pre-commit; reverse it through the DB and re-render (archived specs 015, 034, 041, 042, 044, 046 and 057 keep
  the old order as history)
- [ ] 174. BACKLOG `stable_cursor_field` describes the shipped `Meta.cursor_field` keyset cursors as future work
- [ ] 178. `review_plan.py scope` "Folders touched" (`ScopeReport.folders`) omits a rename's old folder and still names a
  deleted package's integration item, while `--changed` covers both; REVIEW.md says `scope` lists the same changes
- [ ] 181. `utils/querysets.py::applied_order` ignores `extra_order_by`, so a reversed queryset ordered by `extra(order_by=)`
  compiles flipped
- [ ] 183. `ruff format` on an explicit `.md` path rewrites its fenced blocks: pyproject's `exclude` does not stop explicit
  paths
- [ ] 185. WebSocket residual after `1b6a09b1`: the Postgres steady-ping lost-write test has never run (Not defects: a
  sync caller blocked in `async_to_sync` keeping the shared connection is documented behaviour, and the async mutation
  window having no owning spec or card breaks no contract row.)
- [ ] 186. docs/README.md has no consumer-`Prefetch` / `.only()` cooperation sentence and no inert-arm sentence (GLOSSARY has
  both: "`only()` cooperation", from item 83's `548059b3`, and "Membership leaves")
- [ ] 187. The C11 keyset fixes were never run on PostgreSQL's LATERAL path (The workspace / prove_failability `flock`
  rows on Linux or NFS are not a defect: CI runs them on ubuntu.)
- [ ] 190. Seen at `87dc1df7`, re-check: an out-of-range datetime filter value raises an uncoded error (The invalid
  regex and the regex on a UUID field are not defects: both follow django-filter's `regex` lookup, which sends a text
  pattern to the database and types a UUID column's value as a UUID.)
- [ ] 231. KANBAN.md's "`FieldError` keying" card (rendered from the kanban DB) still says
  `validation_error_to_field_errors` is an identity pass-through and that no test covers a multi-word snake_case
  field; both are stale (the key maps and `tests/utils/test_error_keys.py` landed before)
- [ ] 234. Index advisory on a proxy target reads the proxy's empty `Meta.indexes` / `Meta.constraints`
  (`optimizer/nested_planner.py::_model_index_shapes` reads the proxy's `Options`) and recommends an index the concrete
  model already declares (a `GenericRelation` to a proxy)
- [ ] 235. Two comments in `optimizer/nested_planner.py` label a guard "the P2-3 defect" / "the P2-3 false-coverage defect",
  a review label START "No process provenance" bans; restate each as the invariant it guards
- [ ] 241. Duplicate input-object field names escape the value budget:
  `extensions/resource_policy.py::_DocumentWalk.charge_arguments` converts an argument's whole value AST at every reference
  but charges the converted dict, so an overwritten duplicate field is converted and never charged by any value bound (the
  node budget and `max_container_width` alike); 500 spreads of `__typename(a: {k: [1 x2978] k: 1})` walk about 106 ms at
  the default policy and are admitted, against spec-047's "Audited exclusion - `_charge_container`" paragraph ("runs out
  of node budget first")
- [ ] 249. A set-shaped `FilterSet` `Meta.fields` expands in hash order: `{'name', 'description', 'id', 'is_private'}`
  gave four `base_filters` orders under `PYTHONHASHSEED` 1-4 (an `OrderSet` gives one), because `FilterSet.get_fields`
  never calls `utils/inputs.py::canonicalize_set_meta_fields`, whose docstring promises one order under every seed;
  check the generated filter input SDL order too
- [ ] 252. A hook `order_by("<relation>")` on a nested connection's target windows on the `<relation>_id` column
  while the pipeline's compiler expands the name into the related model's `Meta.ordering`: Entry
  `order_by("property")` with `Property.Meta.ordering = ["-name"]` pages `entriesConnection(first: 2)` as {pm, pd}
  optimized and {px, pm} without the optimizer; a random related `Meta.ordering` reached this way also escapes
  `has_random_term`
- [ ] 254. `rest_framework/inputs.py::serializer_schema_fingerprint`'s docstring says "This captures EVERY axis the
  generated input / SDL / reverse map depends on", but `_fingerprint_converter_extra` records only a `ListField`'s direct
  child; retract the sentence to what the fingerprint covers (no code change)
## To do: holes found re-checking the fixes


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
  names. The same question covers `FilterSet` / `OrderSet` / `Filter` class names: the `Meta.fields` rejection, the
  related-target owner label, the order-input leaf rejection, the set-class labels in `filters/sets.py` /
  `orders/sets.py` / `utils/inputs.py`, and the `Projected<Filter>` class name
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
  that owner's visibility. Keep, or fall back to the target model's registered type? It also crosses models: an unwired
  `Sub(Base)` on another model reads `Base`'s owner, so its own-pk filter becomes a `GlobalIDFilter` under a relay owner
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
  fail the frozen view closed; a non-`str` `context["write_alias"]` is a conflict) and 21-23 (field targets, factory
  returns, `Meta` values, set `Meta.fields`, input and policy helpers whose `__class__` raises or claims a type now raise
  the typed error instead of a raw `RuntimeError` / `TypeError`; `Meta.name` / `Meta.description`, a string-helper input
  and a `SESSION_ENGINE` that is a lazy proxy of a `str` are typed rejections; a lazy proxy of a class as a field target
  now reads "requires a DjangoType class") and 221 (`register_mutation()` refuses a protected field declared as a `str`
  subclass whatever its `__eq__`, and a `REQUIRED_FIELDS` that is not a list or tuple or holds a non-string entry, with a
  `ConfigurationError` naming the model instead of a raw `TypeError` / consumer exception)
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
- [ ] 232. CHANGELOG entry for item 92: a Django `ValidationError` raised at save time (`Model.save()` / `delete()`,
  signals, `ModelForm.save()`, `perform_mutate`, register's user save) now returns the `FieldError` envelope on the model,
  form and register flavors instead of "An unexpected error occurred." (0.0.14 masked it); whether to mark it BREAKING
  (a client branching on the top-level error sees `errors` instead) is your call
- [ ] 233. CHANGELOG entry for item 66: the nested-connection composite-index advisory (`WARNING` under `DEBUG`) no longer
  recommends an index naming a multi-table-inheritance parent's column (an inherited order or content-type column), now
  advises for orders naming `pk` or a span Django trims to a local column (`shelf__id`), and names an MTI child's
  parent-link column for an `id` order term
- [ ] 238. CHANGELOG entry for item 67: the docs state that a Django `ValidationError` raised at save time is read as naming
  the mutation's own model fields (one level, never a nested path) and that a serializer fails a nested item at save time by
  raising DRF's `ValidationError` in the nested shape (keyed `shelves.<i>.code`); the fakeshop nested-shelves create reports a
  duplicate shelf code at `shelves.<i>.code` instead of the `__all__` constraint error
- [ ] 240. CHANGELOG entry for item 97: `isNull` on a relation key over a forward `ForeignObject` (any link width), its
  reverse or a `GenericRelation` now builds a Boolean null test like a `ForeignKey`'s instead of raising django-filter's
  "unrecognized field type" `AssertionError` at `FilterSet` class creation (0.0.14 raised for every lookup on a
  `ForeignObject` key); under `unknown_field_behavior` WARN / IGNORE the leaf is now built instead of dropped
- [ ] 245. CHANGELOG entry for item 244: a lone surrogate in a text-keyed relation id or update / delete `id` is a
  field-keyed `invalid` error on every mutation flavor (0.0.14 masked it as "An unexpected error occurred.")
- [ ] 251. CHANGELOG entry for item 224: a `str`-subclass `strictness` (a `StrEnum` member) is stored as the plain mode,
  and `FilterSet` / `OrderSet` `Meta.fields` and `FilterSet` `Meta.exclude` accept `str`-subclass names as the fields they
  spell (0.0.14 refused them as "Cannot classify path" / "entries must be field-name strings")
- [ ] 253. CHANGELOG entry for item 100: a nested connection whose target orders at random (`"?"`, `Random()`) is served
  per parent with the optimizer on, as it is without it (0.0.14 raised "Cannot resolve keyword '?'" for `"?"` and
  minted wrong cursors and pageInfo for `Random()`); under `strictness="raise"` it is an unplanned N+1
- [ ] 108. A serializer-only source over the default `create()` / `update()` (`gs = PrimaryKeyRelatedField(many=True,
  source="genres_id")`) builds; create raises a masked TypeError and update is a silent no-op. Refuse a column-less
  writable source at class creation, as item 103 does for an `attname` source, or leave it to DRF's default `create()` /
  `update()`?
- [ ] 114. Request-rejection precedence: is the admission-seam rewrite still wanted? It changes only which rejection a
  request past the deadline gets (item 113: `FILTER_INVALID` instead of the deadline rejection), touches about 31 files,
  and D-A / D-B below were never ratified. The design (approved 2026-10-08, all 7 decisions;
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
- [ ] 135. A malformed GlobalID in a relation input, single (`categoryId: "not-base64!!"`) or an `[ID!]` element
  (`genres: ["not-base64!!"]`), is a masked top-level error with `data: null` in the model, ModelForm and serializer
  flavors: Strawberry raises `GlobalIDValueError` at the mutation resolver before any package decode, so the field-keyed
  envelope (which a well-formed but missing, wrong-type or hidden id gets) never applies;
  `test_products_api.py::test_create_item_malformed_category_id_is_top_level_coercion_error` pins the outcome but its
  docstring says variable coercion. Return the field-keyed `FieldError` (spec-036 says a malformed relation id surfaces a
  `FieldError` on the field), or keep the top-level error and correct spec-036 and that docstring? Item 191 (a
  committed sibling mutation beside `data: null`) follows the answer
- [ ] 236. One guarded-`isinstance` idiom and one set of hostile test values: `types/base.py` keeps private TypeIs-typed
  `_guarded_isinstance` / `_guarded_issubclass` / `_guarded_narrow`, while `utils/inputs.py`, `filters/sets.py`,
  `sets_mixins.py` and `routers.py` call `exceptions.py::_safe_predicate(isinstance, ...)` and `cast` after it; move the
  typed helpers beside `_safe_predicate` and drop the casts. `tests/_idioms.py::ClassReadRaises` / `ClaimsClass` are
  re-declared locally in `tests/types/test_base.py`, `test_definition_relations.py`, `tests/test_list_field.py`,
  `test_routers.py`, `tests/utils/test_directives.py`, `test_errors.py`, `test_input_values.py` and
  `tests/mutations/test_write_transaction.py`. No defect rides on it (a refactor of private helpers and test idioms): do
  it now, outside a DRY cycle, or leave it to the next DRY cycle?

## Hunt not finished in t3

- [ ] 29. The hunt's final test gate was never run (the Postgres and sharded runs included)
- [ ] 242. Decide removing the dry-0015 worktree, `~/t3code-1cc21548-pre-ff.tgz` and, after item 114 lands,
  `refs/scratch/admission-wip`

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
