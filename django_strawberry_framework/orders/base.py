"""Planned ``RelatedOrder`` primitive for the ordering subsystem."""

# TODO(spec-028-orders-0_0_8 Slice 1): Port the cookbook ``BaseRelatedOrder`` as
# ``RelatedOrder`` using the shared lazy-class resolver.
# Pseudocode:
#   - accept target orderset as a class, absolute import path, or unqualified
#     same-module name.
#   - inherit / reuse ``django_strawberry_framework.sets_mixins.LazyRelatedClassMixin``.
#   - store ``field_name`` as the ORM relation path that parent ordersets expand.
#   - expose ``bind_orderset(parent_cls)`` so ``OrderSetMetaclass`` can stamp the
#     declaring orderset.
#   - resolve lazy string targets during ``OrderSet.get_fields()`` and let
#     finalizer rewrap unresolved imports as ``ConfigurationError``.
