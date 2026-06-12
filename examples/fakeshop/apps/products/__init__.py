"""Products app modeling the seedable catalog used by admin, service, command, and query examples.

It carries Category, Item, Property, and Entry data plus Faker-backed services,
management commands, admin shortcuts, and filter/order sidecars for a practical
catalog-style GraphQL schema.

It is the operational fixture app: services and management commands create users,
seed/delete catalog rows, and prepare sharded data, while admin and schema tests prove
those same paths work both in-process and through live GraphQL HTTP.
"""
