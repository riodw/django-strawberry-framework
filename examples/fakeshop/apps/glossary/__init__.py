"""Glossary app storing documentation terms and spec-term audit rows.

It backs the exported ``docs/GLOSSARY.md`` file and keeps term aliases, categories,
relationships, and spec mentions queryable through the same GraphQL surface used by
the markdown exporter.

It also ties completed design specs back to the board: spec companion CSVs become
``GlossarySpecMention`` rows, and done-card glossary links are reconciled so rendered
documentation, kanban metadata, and GraphQL API reads describe the same vocabulary.
"""
