"""Relation-field resolvers — ``spec-optimizer.md`` O1.

Strawberry's default resolver for an annotated class attribute does
``getattr(source, name)``. For Django relations that returns a
``RelatedManager`` (M2M, reverse FK), which Strawberry rejects with
"Expected Iterable" for list-typed fields. This module attaches a
cardinality-aware resolver per relation field at ``DjangoType``
finalization time so Strawberry's iteration / scalar resolution sees
the right shape.

Forward FK / OneToOne fields would technically work without a custom
resolver (``getattr`` returns the related instance), but they get the
same treatment for consistency and to centralize the prefetch-cache
contract — once ``spec-optimizer.md`` O3+ swaps the manager out, the
resolver shape stays unchanged.

Layered as a sibling of ``types.base`` so the ``DjangoType.__init_subclass__``
pipeline can import ``_attach_relation_resolvers`` without a circular
back-reference (``resolvers.py`` imports nothing from ``base.py``; the
caller pre-computes the field list with ``base._select_fields(meta)`` and
passes it in).
"""

from typing import Any

import strawberry


def _make_relation_resolver(field: Any) -> Any:
    """Generate a resolver for a Django relation field.

    Cardinality-specific shapes:

    - Many-side (M2M, reverse FK): ``list(getattr(root, name).all())``.
      ``manager.all()`` is prefetch-aware (returns the cached list when
      the optimizer has prefetched) so the same shape works on or off
      the optimizer. ``list(...)`` materializes the queryset to a Python
      list, matching strawberry-graphql-django's ``get_result`` shape.
    - Reverse OneToOne (``one_to_one`` and ``auto_created``):
      ``getattr(root, name)`` wrapped in ``try/except DoesNotExist`` so
      the resolver returns ``None`` when the reverse row is absent.
    - Forward FK / forward OneToOne: ``getattr(root, name)`` — returns
      the related instance, or ``None`` if the FK is nullable and unset.
    """
    field_name = field.name

    if field.many_to_many or field.one_to_many:

        def many_resolver(root: Any) -> Any:
            return list(getattr(root, field_name).all())

        many_resolver.__name__ = f"resolve_{field_name}"
        return many_resolver

    if field.one_to_one and getattr(field, "auto_created", False):
        related_does_not_exist = field.related_model.DoesNotExist

        def reverse_one_to_one_resolver(root: Any) -> Any:
            try:
                return getattr(root, field_name)
            except related_does_not_exist:
                return None

        reverse_one_to_one_resolver.__name__ = f"resolve_{field_name}"
        return reverse_one_to_one_resolver

    def forward_resolver(root: Any) -> Any:
        return getattr(root, field_name)

    forward_resolver.__name__ = f"resolve_{field_name}"
    return forward_resolver


def _attach_relation_resolvers(cls: type, fields: list[Any]) -> None:
    """Attach a resolver per relation in the pre-selected ``fields`` list.

    The caller (``DjangoType.__init_subclass__``) computes
    ``base._select_fields(meta)`` once and passes the result here so the
    field walk is not duplicated between annotation building and resolver
    attachment, and so this module avoids importing from ``types.base``
    (which would create a circular dependency).
    """
    for field in fields:
        if not field.is_relation:
            continue
        resolver = _make_relation_resolver(field)
        setattr(cls, field.name, strawberry.field(resolver=resolver))
