"""Library app modeling branch, shelf, book, patron, and loan relations for acceptance queries.

It is the primary relational acceptance surface: live GraphQL tests use it to prove
foreign keys, reverse relations, one-to-one links, many-to-many joins, Relay nodes,
optimizer hints, consumer queryset shaping, and BigInt round-tripping.
"""
