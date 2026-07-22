"""Row-preserving ORM predicate primitives staged by the Part 1 plan.

This module will own correlation and reserved-alias attachment only. Predicate
meaning remains with its caller: django-filter applies one original filter
invocation inside the correlated root, while card 049 will build its own
same-value search disjunctions. Keeping those semantics outside this module
also keeps request values out of the selection optimizer's cross-request
``OptimizationPlan`` cache.
"""

# TODO(docs/row-preserving-predicates-part1-plan.md Slice B): implement the
# neutral correlated-EXISTS primitive without changing ``OptimizationPlan``.
#
# Pseudo:
# - ``correlated_inner_root(queryset)``:
#   1. Read the outer model and resolve ``queryset.db`` once.
#   2. Start from ``model._base_manager.using(resolved_alias)``; the outer
#      queryset already owns manager filtering and visibility, so replaying a
#      filtered default manager here could only create false negatives.
#   3. Correlate with ``filter(pk=OuterRef('pk'))``. This is the sole initial
#      implementation for both scalar and composite primary keys; expand from
#      ``model._meta.pk_fields`` only if the supported-version matrix proves a
#      Django runtime cannot compile the tuple comparison.
#   4. Return the unevaluated inner queryset. It must never execute separately
#      from the outer statement.
# - ``_effective_alias_names(queryset)`` returns one set containing model field
#   names and attnames, literal ``pk``, annotation/alias names, ``extra_select``
#   names, projected/selected names, and every package alias already attached to
#   the query. Read all namespaces before allocating so an alias cannot silently
#   overwrite a consumer expression or compile as ambiguous SQL.
# - ``_next_reserved_alias(queryset, prefix='_dst_predicate_')`` advances a
#   deterministic integer until the candidate is absent from that effective
#   namespace. Recompute from the current queryset on every attachment so
#   repeated compiler calls and existing ``_dst_order_*``/window aliases safely
#   coexist.
# - ``attach_exists(queryset, inner_queryset)``:
#   1. Validate that both are model querysets for the same database alias and
#      that the inner root model matches the outer model. Do NOT reject an
#      evaluated outer queryset: Django permits further construction after
#      evaluation (``.filter()``/``.alias()`` clone the query and run a fresh
#      statement), today's FilterSet path accepts such querysets, and an outer
#      ``_result_cache`` is never embedded in SQL. That the INNER queryset must
#      never execute independently is a documented implementation invariant,
#      not an input guard.
#   2. If ``queryset.query.combinator`` is set, raise ``OptimizerError`` naming
#      the combinator; attaching aliases to UNION/INTERSECT/DIFFERENCE is runtime
#      query-state misuse, not consumer configuration.
#   3. Allocate a collision-free reserved alias, attach
#      ``queryset.alias(**{alias: Exists(inner_queryset)})``, and return the new
#      queryset plus ``Q(**{alias: True})`` for the caller's boolean composition.
#   4. Never call ``filter()``, ``exclude()``, ``distinct()``, or build a
#      predicate body here. The caller owns boolean placement and applies the
#      returned positive branch.
#
# SQL-shape tests in this module assert the emitted statement structure; the
# adapter/live tiers assert the row semantics. Two multiplying-join categories
# must be covered explicitly, and neither subsumes the other:
# - Direct many-to-many: the outer query's ``alias_map`` must exclude the
#   through/child tables, all such joins living inside the correlated EXISTS
#   body.
# - Deep reverse-FK behind a to-one prefix: for a path shaped
#   ``root --forward FK--> intermediate --reverse FK--> membership
#   --forward FK--> terminal``, the emitted OUTER query must exclude BOTH the
#   membership table and the terminal table (all relational joins live inside
#   the correlated EXISTS body). This four-hop shape is the production
#   reproduction where a reverse FK behind a to-one prefix fanned out root rows,
#   and it is a separate case from direct M2M.
# - Same-table inner aliasing (a named shape assertion, not an accident): when
#   the multiplying chain re-enters the root model's own table - the shared
#   fixture does exactly this, ``book__loans`` from a ``Loan`` root puts two
#   aliases of ``library_loan`` inside the existence body, correlated on the
#   outer pk - the compiled subquery must alias the re-entered table correctly
#   and the outer query must still exclude every inner alias.
# The shared acceptance fixture for the deep reverse-FK shape is the fakeshop
# library chain ``Loan.book -> Book.loans -> Loan.patron -> Patron.email`` (four
# seeded loans; ordered primary-key-sequence oracle, not set comparison),
# defined in the Part 1 plan's C.4 section.
#
# Identity/no-op handling stays above ``attach_exists``: a filter invocation
# that returns its correlated inner root by identity must skip this primitive
# before any guard or alias allocation. The existing RelatedFilter tree path in
# ``django_strawberry_framework/filters/sets.py::FilterSet._apply_related_constraints``
# remains a valid, row-preserving ``pk__in`` sibling; neither idiom should
# rewrite the other.
