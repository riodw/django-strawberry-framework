"""Tests for ``DjangoOptimizerExtension`` — query counts, only(), and the downgrade rule.

These tests use ``django_assert_num_queries`` from ``pytest-django`` to
assert the optimizer produces exactly the expected number of SQL round
trips. Each scenario seeds via ``services.seed_data(1)`` so the dataset
shape is deterministic across runs (25 categories, 25 items, 174
properties, 174 entries).
"""

import pytest


@pytest.mark.skip(reason="TODO(slice 4): forward FK -> select_related")
def test_optimizer_applies_select_related_for_forward_fk():
    """A query that selects ``item.category.name`` should join Category in one round trip."""


@pytest.mark.skip(reason="TODO(slice 4): reverse FK -> prefetch_related")
def test_optimizer_applies_prefetch_related_for_reverse_fk():
    """A query that selects ``category.items[*].name`` should prefetch Items in one batch."""


@pytest.mark.skip(reason="TODO(slice 4): M2M -> prefetch_related")
def test_optimizer_applies_prefetch_related_for_m2m():
    """A query that traverses an M2M field should prefetch via the through table.

    Fakeshop has no M2M today; this test will need either a synthetic
    in-test M2M model or a model addition once a natural use case exists.
    """


@pytest.mark.skip(reason="TODO(slice 5): only() projection of selected scalars")
def test_optimizer_applies_only_for_selected_scalars():
    """Selecting only ``id`` and ``name`` should emit ``only("id", "name")`` on the queryset."""


@pytest.mark.skip(reason="TODO(slice 6): downgrade-to-Prefetch when target has custom get_queryset")
def test_optimizer_downgrades_select_related_for_custom_get_queryset():
    """Hidden ``is_private=True`` items must not appear via a select_related join.

    Setup: seed via ``services.seed_data(1)``; flip one item to
    ``is_private=True`` under each category. With ``ItemType.get_queryset``
    filtering ``is_private=False``, querying ``allCategories { items }``
    must yield zero private rows AND must execute exactly two queries
    (root categories + prefetched filtered items).
    """
