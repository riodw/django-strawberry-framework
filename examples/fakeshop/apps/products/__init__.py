"""Products app exercising a seedable catalog, Relay permissions, uploads, and three mutation flavors.

It carries Category, Item, Property, and Entry data plus Faker-backed services,
management commands, admin shortcuts, Relay connections, filter/order sidecars,
cascade visibility, upload inputs, and model/form/serializer mutations.

It is the operational fixture app: services and management commands create users,
seed/delete catalog rows, and prepare sharded data; non-live tests cover admin and
tooling, while schema behavior is exercised both in-process and through live GraphQL HTTP.
"""
