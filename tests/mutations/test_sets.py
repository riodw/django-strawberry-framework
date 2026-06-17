# TODO(spec-036 Slice 2): cover ``DjangoMutation`` declaration and binding.
# Pseudocode:
# - assert bad Meta shapes fail at class creation with ConfigurationError:
#   missing resolvable model, unknown operation, unknown key, bad input class;
# - assert ``_resolve_model`` lets a subclass provide the model without
#   requiring the literal ``Meta.model`` attribute;
# - assert declarations register before finalization and reject late imports
#   after finalization;
# - assert phase-2.5 binding resolves the primary DjangoType and materializes
#   generated input and payload classes;
# - assert no-primary or no-registered-type targets fail loudly at finalization;
# - assert DjangoType ``DEFERRED_META_KEYS`` / ``ALLOWED_META_KEYS`` do not gain
#   mutation-owned keys.
