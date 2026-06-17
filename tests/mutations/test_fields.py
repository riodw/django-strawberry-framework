# TODO(spec-036 Slice 3): cover ``DjangoMutationField`` construction.
# Pseudocode:
# - assert create, update, and delete operations synthesize the correct
#   arguments and payload return type;
# - assert the field works without a class-attribute annotation on the
#   Strawberry Mutation class;
# - assert the payload lazy reference resolves only after finalizer binding;
# - assert sync and async resolver selection mirrors DjangoListField's
#   construction-time and runtime split;
# - assert invalid targets raise ConfigurationError at field construction.
