"""``DjangoMutationField`` factory reserved by spec-036."""

# TODO(spec-036 Slice 3): implement the no-annotation mutation field factory.
# Pseudocode:
# - accept a concrete ``DjangoMutation`` subclass and validate it at field
#   construction time;
# - synthesize the GraphQL argument signature from ``Meta.operation``:
#   create uses ``data: <Model>Input!``, update uses ``id`` plus
#   ``data: <Model>PartialInput!``, and delete uses ``id`` only;
# - generate a resolver whose return annotation uses a Strawberry lazy
#   forward reference to the materialized ``<MutationName>Payload`` type;
# - choose sync versus async resolver behavior with the same construction-time
#   and runtime async-detection split used by DjangoListField;
# - return ``strawberry.field(...)`` so consumers write
#   ``create_item = DjangoMutationField(CreateItem)`` with no class annotation.
