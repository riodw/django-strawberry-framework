# Relation filter input shape — `HIDE_FLAT_FILTERS` (shipped fix)

This covers the one filter-subsystem (`DONE-021-0.0.8`) action: how relation
traversal is exposed in the generated `filter:` input (flat vs nested), and the
`HIDE_FLAT_FILTERS` toggle that controls it. Permissions are *not* part of this —
the row-security cascade that makes both shapes safe is a separate subsystem;
its design and upstream research now live on `TODO-ALPHA-027-0.0.10` in
`KANBAN.md`. Upstream references below point at `~/projects/django-graphene-filters/`
(the cookbook this subsystem was ported from) and `~/projects/strawberry-django-main/`.

## Input shape: support BOTH flat and nested, toggled

Upstream exposes **both** styles and toggles them with `HIDE_FLAT_FILTERS`:

- Default `False` (show both):
  `~/projects/django-graphene-filters/django_graphene_filters/conf.py:35`; the cookbook
  sets it explicitly at
  `~/projects/django-graphene-filters/examples/cookbook/cookbook/settings.py:190-191`.
- The connection field merges flat (graphene-django style) + nested (`filter:` tree)
  arguments, dropping the flat set when `HIDE_FLAT_FILTERS=True`:
  `~/projects/django-graphene-filters/django_graphene_filters/connection_field.py:187-220`.
- Relation traversal is **always nested-only** regardless of the toggle: the flat arg
  set is built from a trimmed filterset that excludes `RelatedFilter`-expanded paths
  (`connection_field.py:222-254`, the `is_expanded_child` check at `:238-242`). So
  `objectTypeName` is never a flat field; it is reached via the nested `objectType`
  ref. Confirmed empirically — `ObjectFilter`'s generated input is
  `[name, description, object_type, values, and, or, not]`.

**`strawberry-graphql-django` parity is the nested shape.** Relations are nested
filter types and scalars are per-field `FilterLookup` operator bags;
`~/projects/strawberry-django-main/strawberry_django/filters.py:164-283`
(`process_filters`) recurses into a nested filter object with an accumulated
`f"{prefix}{field_name}__"` ORM prefix (`:267-274`) — there is no flat relational
input field. The framework's nested `category`/`entries` refs + `name: { exact, … }`
operator bags already match this; the toggle does not touch them.

## The fix in this framework

1. **`HIDE_FLAT_FILTERS`** (default `False`, matching upstream) read from
   `DJANGO_STRAWBERRY_FRAMEWORK` via `getattr(settings, "HIDE_FLAT_FILTERS", False)`.
   When `True`, the flat relational traversal fields (`categoryName`, deep
   `entriesPropertyCategoryName`, …) are omitted from the generated `filter:` input and
   the relation is filtered only through its nested branch. When `False`, both shapes
   are exposed (django-graphene-filters parity, current behavior). Implemented in
   `django_strawberry_framework/filters/inputs.py::_build_input_fields`.

2. **Implementation — the efficient path our architecture enables.** Upstream builds
   the full set then trims via a throwaway dynamic subclass
   (`_get_trimmed_filterset_class`, `connection_field.py:222-254`). Because this
   framework emits a single Strawberry input type from `_build_input_fields`, the trim
   is a one-line conditional **skip** in the grouping loop — the `is_expanded_child`
   test against `related_filters` — so when hidden we never build the operator-bag
   classes for those paths at all (no wasted `build_input_class` calls, no shadow
   subclass).

3. **Both upstreams stay satisfied.** Nested relations + operator bags (the
   strawberry-django shape) are untouched in either toggle position; the flat surface is
   the django-graphene-filters affordance, now controllable. Covered by
   `tests/filters/test_inputs.py::test_build_input_fields_shows_flat_relational_when_hide_flat_filters_false`
   and `…_hides_flat_relational_when_hide_flat_filters_true`.

4. **Row security is out of scope here.** The real boundary is the write-once
   `get_queryset` cascade (`apply_cascade_permissions`), designed and implemented in
   `TODO-ALPHA-027-0.0.10` (see that card for the full upstream model + citations).
   Under it, the flat fields are safe in either toggle position; `HIDE_FLAT_FILTERS` is
   a surface-shape preference, not a security control.
