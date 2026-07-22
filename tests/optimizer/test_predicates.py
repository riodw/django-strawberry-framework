"""Acceptance plan for the neutral row-preserving predicate primitives."""

# TODO(docs/row-preserving-predicates-part1-plan.md Slice B): replace this
# staged test plan with executable ORM tests as the primitive lands.
#
# Pseudo:
# - Seed one parent with two matching children plus direct-only, childless, and
#   nonmatching parents. Build the inner predicate from the root model, attach
#   it, apply the returned positive branch, and assert unique parent PKs.
# - Inspect the OUTER ``query.alias_map``: membership and child tables are
#   absent, ``query.distinct`` is false, SQL contains a correlated ``EXISTS``,
#   and the reserved boolean alias is absent from selected columns.
# - Assert ``correlated_inner_root`` uses ``_base_manager``, preserves an
#   explicit non-default alias, correlates custom single-column PKs, and compiles
#   plus executes composite PK correlation on every supported Django version.
# - Occupy the namespace with model fields/attnames, literal ``pk``, consumer
#   annotations/aliases, ``extra(select=...)``, values projections,
#   ``_dst_order_*``, and window annotations. Repeated attachments must advance
#   deterministically without overwrite or ambiguous SQL.
# - Assert the primitive adds no distinct wrapper to ``count()`` from a plain
#   root queryset. Separately prove compatibility with consumer querysets that
#   were already distinct, annotated, projected, ``only()``, or ``defer()`` and
#   may legitimately count through a subquery.
# - Assert a required attachment to each combined-queryset combinator raises
#   ``OptimizerError`` naming the combinator. Keep no-op identity coverage in
#   the filter adapter tests because ``attach_exists`` is deliberately never
#   called for that branch.
