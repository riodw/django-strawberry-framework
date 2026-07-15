"""Scalars app exercising wire formats, filtering, file/image output, and multipart mutations.

It provides nullable and non-null scalar fixtures, relation edges, and override cases
that let live GraphQL tests pin scalar conversion, serialization, filtering,
schema introspection, structured file/image reads, and model/form Upload mutations.

It keeps scalar edge cases isolated from richer domain fixtures so converter behavior
can be tested directly, then rechecked through live query filters and GraphQL response
serialization without catalog or library model noise.
"""
