# Review feedback - `docs/spec-016-list_field-0_0_7.md`

Reviewed the revised spec against `docs/SPECS/NEW.md`, the current KANBAN card, the installed Strawberry behavior, `graphene_django/fields.py`, and the fakeshop library schema/tests.

## Resolved From Prior Review

The earlier high-risk issues around graphene-django parity, `nullable_list=`, the wrong `(type_cls, info)` resolver pseudocode, and dropping `all_library_branches.order_by("id")` are directionally fixed. The spec now chooses a factory function, drives outer nullability from the consumer annotation, applies `get_queryset` to queryset-shaped consumer resolver returns, and avoids mutating the existing ordered library resolver.

## High

### Resolver signatures still do not build under Strawberry as written

Spec locations: `docs/spec-016-list_field-0_0_7.md:74`, `:232`, `:244`, `:301`, `:315`, `:325-326`, `:363`, `:670`.

The spec repeatedly names the resolver shape as `(root, info, **kwargs)`, and the pseudocode defines `_default(root, info, **kwargs)` / `_wrap(root, info, **kwargs)`. In the installed Strawberry version, `info` must be annotated as `strawberry.types.Info`, and `**kwargs` is not a harmless catch-all for this zero-argument field. A stub matching the spec fails schema construction: unannotated `info` raises `MissingArgumentsAnnotationsError`; annotated `**kwargs: Any` is treated as a GraphQL argument and later fails with `Unexpected type 'typing.Any'`.

Recommendation: rewrite the resolver contract to the shape that works for this field today:

```python
from typing import Any
from strawberry.types import Info

def _default(root: Any, info: Info):
    ...
```

Do the same for `_wrap` and for the public custom-resolver example. Drop `**kwargs` unless this card intentionally adds GraphQL arguments, which it currently does not. If future filter/order args need forwarding, that should land with those argument-bearing specs.

### Async consumer resolvers returning a queryset bypass `get_queryset`

Spec locations: `docs/spec-016-list_field-0_0_7.md:84`, `:244`, `:325-334`, `:350-351`, `:586-587`, `:651`, `:680`.

The spec promises `target_type.get_queryset(qs, info)` is applied to every consumer resolver return value that is a `Manager` or `QuerySet`. The pseudocode only checks the immediate return from `user_resolver(...)`. If the consumer resolver is `async def` and returns a `QuerySet`, the immediate value is a coroutine, so the wrapper falls through at line 334 and returns it unchanged. Strawberry will await it later, but the field wrapper has already missed the chance to apply `get_queryset`.

Recommendation: make the wrapper await awaitable consumer results before deciding whether the final value is a `Manager` / `QuerySet`, or explicitly declare async custom resolvers out of scope. The better fit with the rest of the spec is to support them and add two tests: async custom resolver returning a `QuerySet` gets `get_queryset`, and async custom resolver returning a Python `list` passes through.

### The fakeshop plan no longer satisfies the KANBAN card's replacement requirement

Spec locations: `docs/spec-016-list_field-0_0_7.md:96`, `:117-125`, `:142`, `:155`, `:501-516`, `:674`.

The KANBAN card's Definition of done says live HTTP coverage should replace one hand-rolled `all_library_*` resolver. The revised spec instead adds a sibling `all_library_branches_via_list_field` and leaves all existing resolvers untouched. That is a reasonable risk-reduction move for ordering, but it no longer removes any example boilerplate and no longer satisfies the card as written.

Recommendation: either change the spec back to replacing one resolver while preserving deterministic behavior, or explicitly call this out as an intentional departure from the KANBAN card and require the implementation slice to update the card's wording when it moves to Done. The current spec presents the add-only strategy as if it still fulfills the original replacement scope.

## Medium

### Manager coercion is described as optimizer-owned even though the field wrapper must do it

Spec location: `docs/spec-016-list_field-0_0_7.md:178`.

The borrowing-posture section says `Manager -> QuerySet` coercion happens automatically inside `DjangoOptimizerExtension._optimize`, but the field wrapper must also coerce `Manager` before applying `target_type.get_queryset`. The pseudocode correctly does `result.all()` before the hook; the prose should match that. Otherwise an implementer could remove the wrapper-side coercion and silently skip `get_queryset` for `Model.objects` returns.

Recommendation: say the field wrapper performs Manager coercion for visibility-hook correctness, while the optimizer's Manager coercion remains a downstream safety net for non-`DjangoListField` root resolvers.

### Several revision-tracking lines are stale

Spec locations: `docs/spec-016-list_field-0_0_7.md:4`, `:538-551`.

The header still says `Status: draft (revision 1, initial)` even though the body has Revision 3. The implementation plan says "five commits" while the table and next paragraph describe six slices including Slice 0.

Recommendation: update the status line to revision 3 and change the implementation-plan prose to "six slices" or clarify that Slice 0 is not a commit.

## Low

### A few add-vs-replace references remain stale

Spec locations: `docs/spec-016-list_field-0_0_7.md:104`, `:142`.

The Slice 5 `TODAY.md` bullet still says "if the new resolver replaces a hand-rolled one", and Current state says the library app is the home "where one resolver-replacement is enough". Both now conflict with the add-only strategy.

Recommendation: update both to the new sibling-field language.
