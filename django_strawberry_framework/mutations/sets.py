"""``DjangoMutation`` declaration and finalizer binding reserved by spec-036."""

# TODO(spec-036 Slice 2): implement the ``DjangoMutation`` base and metaclass.
# Pseudocode:
# - collect nested ``Meta`` options at class creation: operation, model,
#   input_class, partial_input_class, fields, and exclude;
# - resolve the model through an overridable ``_resolve_model(meta)`` seam so
#   future form and serializer flavors can derive the model without Meta.model;
# - reject unknown ``Meta`` keys, unknown operations, missing resolvable models,
#   and custom input classes that are not Strawberry input types;
# - register mutation classes for the finalizer binder and reject late
#   declarations after ``registry.mark_finalized()``;
# - during phase 2.5, resolve the model's primary DjangoType, then ask
#   ``inputs.py`` to materialize generated create/update input classes and the
#   per-mutation payload wrapper;
# - keep mutation Meta validation separate from DjangoType Meta validation.
