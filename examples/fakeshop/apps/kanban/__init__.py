"""Kanban app storing board cards, dependencies, docs prose, and markdown export metadata.

It is the database source for the root ``KANBAN.md`` export, including card ordering,
dependency integrity, release targeting, glossary links, and reusable prose sections
shared with other docs-as-data exporters.

It owns the board invariants rather than leaving them in importer scripts: card numbers,
status placement, dependency edges, dependency prose, card references, and reusable
BoardDoc prose are validated in app services/signals so every entry point behaves the
same way.
"""
