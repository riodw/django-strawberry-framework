"""Scalars app modeling converter specimens for wire-format and filter coverage.

It provides nullable and non-null scalar fixtures, relation edges, and override cases
that let live GraphQL tests pin scalar conversion, serialization, filtering, and
schema introspection behavior.

It keeps scalar edge cases isolated from richer domain fixtures so converter behavior
can be tested directly, then rechecked through live query filters and GraphQL response
serialization without catalog or library model noise.
"""
