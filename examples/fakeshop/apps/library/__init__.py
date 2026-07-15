"""Library app exercising relation graphs, keyset connections, and live model/form/serializer mutations.

It is the primary relational acceptance surface: live GraphQL tests use it to prove
foreign keys, reverse relations, one-to-one links, many-to-many joins, Relay nodes,
optimizer hints, consumer queryset shaping, BigInt round-tripping, periodical/issue
keyset connections, and mutation edge cases including raw-PK relations and nested writes.

It deliberately stays service-free: tests create rows inline so relation behavior,
queryset planning, and computed fields remain visible without a fixture abstraction
hiding the model graph being exercised.
"""
