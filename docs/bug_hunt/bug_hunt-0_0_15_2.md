# Bug hunt 0.0.15 (2): to-do list

Every finding from the 0.0.15 hunt in the t3 worktree (never merged), plus bugs found while fixing them.
Each one is verified on main, fixed at the root, checked by a second agent, landed, then deleted from t3.

Progress: 28 done, 46 to do.

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

## To do: t3 hunt findings

- [ ] 12. Nested forward-FK / OneToOne resolvers never check the request deadline
- [ ] 14. README says integer `in: []` matches nothing; t3 saw it match everything. Check which is right

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
- [ ] 48. `BLANK_CHOICE` marker breaks under copy / pickle
- [ ] 49. `serializer_field_description` re-raises `KeyboardInterrupt`
- [ ] 50. SKIP hint drops relation columns from `.only()`, so every row is fetched again (unverified)
- [ ] 51. `OrderSet` `"__all__"` leaves out `ForeignObject` fields (unverified)
- [ ] 52. Connection resolvers send raw exception text to the client (unverified)
- [ ] 56. Two writable serializer fields can write the same FK column (`category` and `source="category_id"`)
- [ ] 74. A consumer `select_related` on a forward FK the query never selects, combined with the optimizer's `.only()`, raises
  Django's "cannot be both deferred and traversed" (`Entry.objects.select_related("property")` with `{ entries { value item { name } } }`)

## To do: holes found re-checking the fixes

- [ ] 61. Three `FilterSet`s in a `RelatedFilter` cycle: the flat filters exposed depend on type declaration order
- [ ] 62. A declared flat `ChoiceField` over a grouped-choices column is refused since item 35 (worked before); the refusal's message is
  also wrong for a column no type exposes
- [ ] 63. `after` cursor at `sys.maxsize - 1 - page` with `first: 0` / `last: 0` raises Strawberry's assert instead of an empty page
- [ ] 64. Two cursor-decoder guards no test pins (`isascii`, the nested-window decode)
- [ ] 65. `iExact: BLANK` on a choice column matches every row
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
- [ ] 73. A set subclass used only as a `RelatedFilter` / `RelatedOrder` target, never wired to a type, inherits its base's owner and
  that owner's visibility. Keep, or fall back to the target model's registered type?

## Hunt not finished in t3

- [ ] 28. Deep dive 3 (authorization on deferred paths) is blocked; its findings are items 12 and 13
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
