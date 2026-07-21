"""Composite-index advisory unit matrix for nested connection strategies.

Pins ``nested_planner.py``'s dev-mode advisory: it prefix-matches a child
model's REPRESENTED physical index shapes - unconditional field-based
``Meta.indexes`` / ``UniqueConstraint`` / legacy ``unique_together``, plus
single-column ``db_index`` / ``unique`` / FK auto-index - against a nested
window's leading ``(content_type_id?, connector, order terms..., pk)`` shape,
warns only under ``settings.DEBUG``, and - the fail-soft contract - stays SILENT
unless absence is PROVEN from fully-inspectable metadata. That tri-state spans
BOTH ends of the comparison. Index side: an expression index, a PARTIAL index /
unique constraint (a ``condition``), or a migration-lagged field name leaves
coverage UNKNOWN (never falsely covered). Order side: an effective ORDER term
that is not a local concrete column (a related span, a ``Lower(...)`` expression,
an alias, an unresolvable name) OR that carries explicit ``NULLS FIRST`` /
``LAST`` leaves the SQL order only partially understood - either UNKNOWN keeps
the advisory silent (never a false-positive warning, never a suffix-only coverage
claim). Access method is load-bearing: only a plain ``models.Index`` or the
PostgreSQL ``BTreeIndex`` builds the ordinary ordered B-tree the advisory reasons
about, so a ``GinIndex`` / ``GistIndex`` / ``HashIndex`` / ``BrinIndex`` /
``SpGistIndex``, a custom ``Index`` subclass, a non-default opclass, or a
descending column on a backend without index-column ordering all leave coverage
UNKNOWN (never falsely covered). Equality-constrained columns (the connector / morph prefix) are STRIPPED
from the within-partition order before comparison, so an order led by (or
threading) the partition key is not falsely reported absent or recommended with a
duplicated column. Direction is carried through the comparison so a mixed
``title ASC, id DESC`` is served only by the requested order or its FULL reverse,
and a ``GenericRelation`` window recommends the ``content_type_id``-prefixed
composite. The advisory is deferred until a strategy ACCEPTS a window (a refusing
custom strategy advises nothing), and a bounded, strategy- and
request-independent dedup makes one plan shape warn at most once even when a
custom-``get_queryset`` plan is rebuilt every request. Package tier: the helpers
operate on model ``_meta`` and a strategy-agnostic join descriptor, unreachable
from a live /graphql query (no observable schema surface); the deferral is driven
through an in-process schema.
"""

from types import SimpleNamespace

import pytest
from apps.library.models import Branch, TaggedItem
from django.contrib.postgres.indexes import (
    BrinIndex,
    BTreeIndex,
    GinIndex,
    GistIndex,
    HashIndex,
    SpGistIndex,
)
from django.db import models
from django.db.models.functions import Lower
from django.test import override_settings

from django_strawberry_framework.optimizer import logger as optimizer_logger
from django_strawberry_framework.optimizer import nested_planner
from django_strawberry_framework.optimizer.join_taxonomy import classify_relation_join
from django_strawberry_framework.optimizer.nested_planner import (
    _INDEX_ABSENT,
    _INDEX_COVERED,
    _INDEX_UNKNOWN,
    _advise_composite_index,
    _concrete_order_terms,
    _index_coverage,
    _index_leading_terms,
    clear_index_advisory_dedup,
)


@pytest.fixture(autouse=True)
def _reset_index_advisory_dedup():
    """Clear the advisory dedup around every test in this module.

    The bounded ``_index_advisory_seen`` LRU makes one plan shape warn at most
    once process-wide; without a per-test reset, a shape recorded by an earlier
    test (or an earlier DEBUG-toggle of the SAME shape) would silence a later
    test that asserts the warning. Mirrors the registry / connection-type cache
    reset fixtures in ``tests/conftest.py``.
    """
    clear_index_advisory_dedup()
    yield
    clear_index_advisory_dedup()


class _IdxParent(models.Model):
    """Unmanaged partition parent for advisory metadata-only tests."""

    class Meta:
        app_label = "tests"
        managed = False


class _IdxChildBare(models.Model):
    """Child with only the ForeignKey auto-index (no ``Meta.indexes``)."""

    parent = models.ForeignKey(_IdxParent, on_delete=models.CASCADE, related_name="bare")
    title = models.CharField(max_length=50)

    class Meta:
        app_label = "tests"
        managed = False
        ordering = ("title", "id")


class _IdxChildComposite(models.Model):
    """Child carrying a composite index covering the window's leading columns."""

    parent = models.ForeignKey(_IdxParent, on_delete=models.CASCADE, related_name="composite")
    title = models.CharField(max_length=50)

    class Meta:
        app_label = "tests"
        managed = False
        ordering = ("title", "id")
        indexes = [models.Index(fields=["parent", "title", "id"])]


class _IdxChildExpr(models.Model):
    """Child whose only index is an expression index (no ``.fields``)."""

    parent = models.ForeignKey(_IdxParent, on_delete=models.CASCADE, related_name="expr")
    title = models.CharField(max_length=50)

    class Meta:
        app_label = "tests"
        managed = False
        ordering = ("title", "id")
        indexes = [models.Index(Lower("title"), name="idx_expr_lower_title")]


class _IdxChildMixed(models.Model):
    """Child whose index mirrors a mixed-direction order ``title ASC, id DESC``."""

    parent = models.ForeignKey(_IdxParent, on_delete=models.CASCADE, related_name="mixed")
    title = models.CharField(max_length=50)

    class Meta:
        app_label = "tests"
        managed = False
        ordering = ("title", "-id")
        indexes = [models.Index(fields=["parent", "title", "-id"])]


class _IdxChildReversed(models.Model):
    """Child whose index is the FULL reverse of an ascending order ``title, id``."""

    parent = models.ForeignKey(_IdxParent, on_delete=models.CASCADE, related_name="reversed")
    title = models.CharField(max_length=50)

    class Meta:
        app_label = "tests"
        managed = False
        ordering = ("title", "id")
        indexes = [models.Index(fields=["parent", "-title", "-id"])]


class _IdxChildPartial(models.Model):
    """Child whose only composite index is PARTIAL (carries a ``condition``).

    PostgreSQL uses a partial index only for queries whose predicate implies its
    condition; the general nested window does not, so its exact-column shape must
    NOT be read as covering (the P2-3 false-coverage defect) - it leaves absence
    UNPROVEN instead.
    """

    parent = models.ForeignKey(_IdxParent, on_delete=models.CASCADE, related_name="partial")
    title = models.CharField(max_length=50)

    class Meta:
        app_label = "tests"
        managed = False
        ordering = ("title", "id")
        indexes = [
            models.Index(
                fields=["parent", "title", "id"],
                name="idx_partial_active",
                condition=models.Q(title__gt=""),
            ),
        ]


class _IdxChildUniqueConstraint(models.Model):
    """Child covering the window via an unconditional composite ``UniqueConstraint``.

    A unique constraint materializes a usable ascending btree, so an exact-column
    one must be recognized as covering - a consumer that already declared it must
    NOT be told to create the same physical index again (the P2-3 false-absence
    defect).
    """

    parent = models.ForeignKey(_IdxParent, on_delete=models.CASCADE, related_name="uniqc")
    title = models.CharField(max_length=50)

    class Meta:
        app_label = "tests"
        managed = False
        ordering = ("title", "id")
        constraints = [
            models.UniqueConstraint(fields=["parent", "title", "id"], name="uq_parent_title_id"),
        ]


class _IdxChildPartialUniqueConstraint(models.Model):
    """Child whose only unique constraint is PARTIAL (a ``condition``) -> uninspectable."""

    parent = models.ForeignKey(_IdxParent, on_delete=models.CASCADE, related_name="uniqcpartial")
    title = models.CharField(max_length=50)

    class Meta:
        app_label = "tests"
        managed = False
        ordering = ("title", "id")
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "title", "id"],
                name="uq_partial_parent_title_id",
                condition=models.Q(title__gt=""),
            ),
        ]


class _IdxChildOpclassUniqueConstraint(models.Model):
    """Child whose only unique constraint carries NON-DEFAULT opclasses -> uninspectable.

    A non-default opclass (``varchar_pattern_ops`` etc.) is chosen for a lookup
    semantics that need not provide the window's ordinary ordering, so an
    otherwise exact-column unique constraint must NOT be read as an ascending
    B-tree that covers the sort - the ``UniqueConstraint.opclasses`` escape,
    exactly the ``Index.opclasses`` case one level up.
    """

    parent = models.ForeignKey(_IdxParent, on_delete=models.CASCADE, related_name="uniqcopclass")
    title = models.CharField(max_length=50)

    class Meta:
        app_label = "tests"
        managed = False
        ordering = ("title", "id")
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "title", "id"],
                name="uq_opclass_parent_title_id",
                opclasses=["int4_ops", "varchar_pattern_ops", "int4_ops"],
            ),
        ]


class _IdxChildUniqueTogether(models.Model):
    """Child covering the window via legacy ``unique_together``."""

    parent = models.ForeignKey(_IdxParent, on_delete=models.CASCADE, related_name="uniqt")
    title = models.CharField(max_length=50)

    class Meta:
        app_label = "tests"
        managed = False
        ordering = ("title", "id")
        unique_together = (("parent", "title", "id"),)


class _IdxChildCheckConstraint(models.Model):
    """Child whose only ``Meta.constraints`` entry is a ``CheckConstraint``.

    A ``CheckConstraint`` (like an ``ExclusionConstraint``) is not a unique
    btree, so it is neither a coverage shape nor uninspectable - the shape
    inventory simply skips it. With no covering index the window is PROVEN
    absent, unaffected by the constraint's presence.
    """

    parent = models.ForeignKey(_IdxParent, on_delete=models.CASCADE, related_name="ckc")
    title = models.CharField(max_length=50)

    class Meta:
        app_label = "tests"
        managed = False
        ordering = ("title", "id")
        constraints = [
            models.CheckConstraint(condition=models.Q(title__gt=""), name="ck_title_nonempty"),
        ]


class _IdxChildUniqueConstraintMigrationLag(models.Model):
    """Child whose composite ``UniqueConstraint`` names a field the model no longer has.

    A migration-lagged constraint field (here ``ghost``) cannot be resolved to a
    column, so the shape is UNINSPECTABLE rather than a covering ascending btree -
    absence stays unproven instead of trusting a stale unique shape.
    """

    parent = models.ForeignKey(_IdxParent, on_delete=models.CASCADE, related_name="uclag")
    title = models.CharField(max_length=50)

    class Meta:
        app_label = "tests"
        managed = False
        ordering = ("title", "id")
        constraints = [
            models.UniqueConstraint(fields=["parent", "title", "ghost"], name="uq_lag_ghost"),
        ]


class _IdxChildUniqueTogetherMigrationLag(models.Model):
    """Child whose legacy ``unique_together`` names a field the model no longer has.

    The ``unique_together`` twin of the migration-lag case: an unresolvable name
    leaves the shape uninspectable, so absence stays unproven.
    """

    parent = models.ForeignKey(_IdxParent, on_delete=models.CASCADE, related_name="utlag")
    title = models.CharField(max_length=50)

    class Meta:
        app_label = "tests"
        managed = False
        ordering = ("title", "id")
        unique_together = (("parent", "ghost"),)


class _IdxChildGin(models.Model):
    """Child whose only composite ``Meta.indexes`` entry is a NON-B-tree ``GinIndex``.

    A ``GinIndex`` inherits ``Index.fields`` yet backs an inverted-index access
    method that cannot serve an ordinary multi-column ``ORDER BY``. Its exact
    columns must therefore NOT be read as covering the window (the false-``covered``
    defect for non-B-tree indexes) - the FK auto-index still covers a
    connector-only window, but a window that also orders must fall to UNKNOWN.
    """

    parent = models.ForeignKey(_IdxParent, on_delete=models.CASCADE, related_name="gin")
    title = models.CharField(max_length=50)

    class Meta:
        app_label = "tests"
        managed = False
        ordering = ("title", "id")
        indexes = [GinIndex(fields=["parent", "title", "id"], name="idx_gin_cover")]


class TestIndexLeadingTerms:
    """``_index_leading_terms`` maps index field names to ``(attname, descending)``."""

    def test_maps_field_names_to_terms(self) -> None:
        """A composite index resolves each field name to ``(attname, direction)``."""
        index = _IdxChildComposite._meta.indexes[0]
        assert _index_leading_terms(_IdxChildComposite._meta, index) == [
            ("parent_id", False),
            ("title", False),
            ("id", False),
        ]

    def test_carries_descending_direction(self) -> None:
        """A ``-``-prefixed field resolves to the same attname flagged descending."""
        index = models.Index(fields=["parent", "-title"], name="idx_desc_title")
        assert _index_leading_terms(_IdxChildComposite._meta, index) == [
            ("parent_id", False),
            ("title", True),
        ]

    def test_expression_index_returns_none(self) -> None:
        """An expression index (no ``.fields``) is uninspectable -> ``None``."""
        index = _IdxChildExpr._meta.indexes[0]
        assert _index_leading_terms(_IdxChildExpr._meta, index) is None

    def test_unresolvable_field_returns_none(self) -> None:
        """A field name that no longer resolves degrades to ``None``, not raise."""
        index = models.Index(fields=["nope"], name="idx_missing_field")
        assert _index_leading_terms(_IdxChildComposite._meta, index) is None

    def test_btree_index_is_inspectable(self) -> None:
        """PostgreSQL ``BTreeIndex`` is an ordinary ordered B-tree -> terms, like ``models.Index``."""
        index = BTreeIndex(fields=["parent", "title", "id"], name="idx_btree_cover")
        assert _index_leading_terms(_IdxChildComposite._meta, index) == [
            ("parent_id", False),
            ("title", False),
            ("id", False),
        ]

    @pytest.mark.parametrize(
        "index_cls",
        [
            GinIndex,
            GistIndex,
            HashIndex,
            BrinIndex,
            SpGistIndex,
        ],
    )
    def test_non_btree_access_method_is_uninspectable(self, index_cls) -> None:
        """A non-B-tree access method cannot serve an ordinary ORDER BY -> ``None`` (never covered)."""
        index = index_cls(fields=["title"], name=f"idx_{index_cls.__name__.lower()}")
        assert _index_leading_terms(_IdxChildComposite._meta, index) is None

    def test_custom_index_subclass_is_uninspectable(self) -> None:
        """A custom ``Index`` subclass we cannot vouch for degrades to ``None``, not covered."""

        class _CustomIndex(models.Index):
            pass

        index = _CustomIndex(fields=["parent", "title"], name="idx_custom_subclass")
        assert _index_leading_terms(_IdxChildComposite._meta, index) is None

    def test_non_default_opclass_is_uninspectable(self) -> None:
        """A non-default opclass need not provide ordinary ordering -> ``None`` (never covered)."""
        index = models.Index(
            fields=["title"],
            name="idx_opclass",
            opclasses=["varchar_pattern_ops"],
        )
        assert _index_leading_terms(_IdxChildComposite._meta, index) is None

    def test_descending_column_without_backend_ordering_is_uninspectable(
        self,
        monkeypatch,
    ) -> None:
        """A ``-``-column is a physical DESC index ONLY where the backend supports it.

        Where it does not, Django silently builds a plain ascending index, so the
        ``("id", True)`` reading would be wrong; the classifier fails soft to
        ``None`` (UNKNOWN) rather than making a backend-dependent coverage claim.
        """
        monkeypatch.setattr(
            nested_planner,
            "_every_backend_supports_index_column_ordering",
            lambda: False,
        )
        index = models.Index(fields=["parent", "title", "-id"], name="idx_desc_unsupported")
        assert _index_leading_terms(_IdxChildComposite._meta, index) is None

    def test_descending_column_with_backend_ordering_is_inspectable(self, monkeypatch) -> None:
        """With backend index-column ordering, a ``-``-column keeps its descending direction."""
        monkeypatch.setattr(
            nested_planner,
            "_every_backend_supports_index_column_ordering",
            lambda: True,
        )
        index = models.Index(fields=["parent", "title", "-id"], name="idx_desc_supported")
        assert _index_leading_terms(_IdxChildComposite._meta, index) == [
            ("parent_id", False),
            ("title", False),
            ("id", True),
        ]


class _FakeConnections:
    """A minimal ``connections``-handler stand-in: iterate alias names, index to a backend."""

    def __init__(self, by_alias: dict) -> None:
        self._by_alias = by_alias

    def __iter__(self):
        return iter(self._by_alias)

    def __getitem__(self, alias: str):
        return self._by_alias[alias]


def _fake_backend(*, supports_ordering: bool) -> SimpleNamespace:
    return SimpleNamespace(
        features=SimpleNamespace(supports_index_column_ordering=supports_ordering),
    )


class TestEveryBackendSupportsIndexColumnOrdering:
    """``_every_backend_supports_index_column_ordering`` trusts a DESC term only when EVERY
    configured backend can store it; fail-soft to ``False`` on any error.

    A nested plan is backend-neutral and cache-shared, so it cannot consult one
    unhinted route and treat the answer as universal: a divergent router could
    return a direction-capable default at plan time while the same cached plan
    later runs on a shard that silently drops the direction (the alias-early
    class of error). Requiring universal support closes that gap.
    """

    def test_true_on_the_test_backend(self) -> None:
        """The real (SQLite) test database supports index-column ordering -> True."""
        assert nested_planner._every_backend_supports_index_column_ordering() is True

    def test_divergent_alias_without_support_is_unproven(self, monkeypatch) -> None:
        """One incapable alias makes a DESC term unproven even when the default supports it."""
        monkeypatch.setattr(
            "django.db.connections",
            _FakeConnections(
                {
                    "default": _fake_backend(supports_ordering=True),
                    "shard_b": _fake_backend(supports_ordering=False),
                },
            ),
        )
        assert nested_planner._every_backend_supports_index_column_ordering() is False

    def test_all_aliases_supporting_is_true(self, monkeypatch) -> None:
        """When every configured alias supports ordering, the DESC term is trusted."""
        monkeypatch.setattr(
            "django.db.connections",
            _FakeConnections(
                {
                    "default": _fake_backend(supports_ordering=True),
                    "shard_b": _fake_backend(supports_ordering=True),
                },
            ),
        )
        assert nested_planner._every_backend_supports_index_column_ordering() is True

    def test_empty_configuration_is_unproven(self, monkeypatch) -> None:
        """No configured databases -> nothing proves support -> ``False`` (unknown)."""
        monkeypatch.setattr("django.db.connections", _FakeConnections({}))
        assert nested_planner._every_backend_supports_index_column_ordering() is False

    def test_enumeration_failure_is_fail_soft_false(self, monkeypatch) -> None:
        """A connection-handler error at plan time degrades to ``False`` (index UNKNOWN)."""

        class _Boom:
            def __iter__(self):
                raise RuntimeError("connections unavailable at plan time")

        monkeypatch.setattr("django.db.connections", _Boom())
        assert nested_planner._every_backend_supports_index_column_ordering() is False


class TestConcreteOrderTerms:
    """``_concrete_order_terms`` is tri-state: full terms, or ``None`` when any is not local.

    The P2 fix moves the fail-soft tri-state upstream to ORDER parsing: any term
    that is not a local concrete ``(attname, direction)`` (a related span, an
    expression, an alias, an unresolvable name) makes the SQL order only
    partially understood, so the helper returns ``None`` and the advisory stays
    silent rather than claim a false coverage from the remaining suffix.
    """

    def test_carries_mixed_directions(self) -> None:
        """A fully-local mixed order yields the requested per-column directions."""
        assert _concrete_order_terms(["title", "-id"], _IdxChildBare) == [
            ("title", False),
            ("id", True),
        ]

    def test_related_span_lookup_is_unknown(self) -> None:
        """A ``__``-spanning lookup is not a local concrete column -> ``None`` (unknown)."""
        assert _concrete_order_terms(["parent__title", "id"], _IdxChildBare) is None

    def test_expression_entry_is_unknown(self) -> None:
        """An arbitrary expression (``Lower("title")``) has no local column -> ``None``."""
        assert _concrete_order_terms([Lower("title"), "id"], _IdxChildBare) is None

    def test_unparsable_entry_is_unknown(self) -> None:
        """A bare ``"-"`` entry has no resolvable name -> ``None``, not raised."""
        assert _concrete_order_terms(["-", "title"], _IdxChildBare) is None

    def test_accepts_a_bare_attname(self) -> None:
        """An entry already spelled as an attname resolves to itself."""
        assert _concrete_order_terms(["parent_id"], _IdxChildBare) == [("parent_id", False)]

    def test_unresolvable_name_is_unknown(self) -> None:
        """A name that is neither a field nor an attname (an alias) -> ``None``."""
        assert _concrete_order_terms(["bogus", "id"], _IdxChildBare) is None

    def test_dedupes_repeated_column(self) -> None:
        """A column repeated in the order is emitted once (first direction wins)."""
        assert _concrete_order_terms(["title", "title"], _IdxChildBare) == [("title", False)]

    def test_nulls_first_placement_is_unknown(self) -> None:
        """An ``OrderBy`` with explicit ``nulls_first`` is not index-provable -> ``None``.

        The P2 fix: ``title ASC NULLS FIRST`` cannot be proven served by a plain
        ``Meta.indexes`` term (default backend NULL placement), so the whole order
        is UNKNOWN rather than collapsing to a bare ``("title", False)``.
        """
        assert (
            _concrete_order_terms([models.F("title").asc(nulls_first=True), "id"], _IdxChildBare)
            is None
        )

    def test_nulls_last_placement_is_unknown(self) -> None:
        """An ``OrderBy`` with explicit ``nulls_last`` is likewise UNKNOWN -> ``None``."""
        assert (
            _concrete_order_terms([models.F("title").desc(nulls_last=True)], _IdxChildBare) is None
        )


class TestIndexCoverage:
    """``_index_coverage`` is tri-state: covered / absent / unknown."""

    def test_composite_index_covers(self) -> None:
        """The composite index's leading columns satisfy the full shape."""
        assert (
            _index_coverage(
                _IdxChildComposite,
                ["parent_id"],
                [("title", False), ("id", False)],
            )
            == _INDEX_COVERED
        )

    def test_no_index_multi_column_is_absent(self) -> None:
        """A fully-inspectable bare child proves absence for a multi-column shape."""
        assert (
            _index_coverage(_IdxChildBare, ["parent_id"], [("title", False), ("id", False)])
            == _INDEX_ABSENT
        )

    def test_single_column_covered_by_fk_auto_index(self) -> None:
        """A single equality column rides the ForeignKey's automatic ``db_index``."""
        assert _index_coverage(_IdxChildBare, ["parent_id"], []) == _INDEX_COVERED

    def test_expression_index_is_unknown(self) -> None:
        """An unclassifiable expression index leaves absence UNPROVEN -> unknown."""
        assert (
            _index_coverage(_IdxChildExpr, ["parent_id"], [("title", False), ("id", False)])
            == _INDEX_UNKNOWN
        )

    def test_index_shorter_than_equality_prefix_does_not_cover(self) -> None:
        """An index with fewer columns than the equality prefix cannot cover it."""
        assert (
            _index_coverage(
                _IdxChildComposite,
                [
                    "parent_id",
                    "title",
                    "id",
                    "missing",
                ],
                [],
            )
            == _INDEX_ABSENT
        )

    def test_index_not_leading_with_equality_columns_does_not_cover(self) -> None:
        """An index whose leading column is not the equality prefix does not cover."""
        assert _index_coverage(_IdxChildComposite, ["title"], [("id", False)]) == _INDEX_ABSENT

    def test_partial_index_is_not_universally_covered(self) -> None:
        """A PARTIAL exact-column index leaves absence UNPROVEN -> unknown, never covered.

        The P2-3 fix: a partial index (carrying a ``condition``) is uninspectable,
        so the model that has ONLY a partial index on the right columns is
        ``unknown`` rather than ``covered`` - the general page cannot rely on it.
        """
        assert (
            _index_coverage(_IdxChildPartial, ["parent_id"], [("title", False), ("id", False)])
            == _INDEX_UNKNOWN
        )

    def test_unconditional_unique_constraint_covers(self) -> None:
        """An exact-column unconditional ``UniqueConstraint`` covers the window shape.

        The P2-3 fix: a consumer who already declared the composite unique
        constraint must NOT be warned to create the same physical index again.
        """
        assert (
            _index_coverage(
                _IdxChildUniqueConstraint,
                ["parent_id"],
                [("title", False), ("id", False)],
            )
            == _INDEX_COVERED
        )

    def test_partial_unique_constraint_is_unknown(self) -> None:
        """A PARTIAL unique constraint is uninspectable -> unknown, never covered."""
        assert (
            _index_coverage(
                _IdxChildPartialUniqueConstraint,
                ["parent_id"],
                [("title", False), ("id", False)],
            )
            == _INDEX_UNKNOWN
        )

    def test_opclass_unique_constraint_is_unknown(self) -> None:
        """A unique constraint with non-default opclasses is uninspectable -> unknown.

        The ``UniqueConstraint.opclasses`` escape (P2): an exact-column unique
        constraint whose opclasses are non-default would otherwise be read as an
        ordinary ascending B-tree and falsely suppress the advisory - the same
        capability gate ``_index_leading_terms`` applies to ``Index.opclasses``.
        """
        assert (
            _index_coverage(
                _IdxChildOpclassUniqueConstraint,
                ["parent_id"],
                [("title", False), ("id", False)],
            )
            == _INDEX_UNKNOWN
        )

    def test_unique_together_covers(self) -> None:
        """Legacy ``unique_together`` participates in coverage while Django exposes it."""
        assert (
            _index_coverage(
                _IdxChildUniqueTogether,
                ["parent_id"],
                [("title", False), ("id", False)],
            )
            == _INDEX_COVERED
        )

    def test_check_constraint_is_skipped_not_uninspectable(self) -> None:
        """A ``CheckConstraint`` is neither a coverage shape nor uninspectable.

        It is skipped by the shape inventory, so a model whose only constraint is
        a ``CheckConstraint`` and which has no covering index leaves the window
        PROVEN absent (the constraint never muddies the tri-state to unknown).
        """
        assert (
            _index_coverage(
                _IdxChildCheckConstraint,
                ["parent_id"],
                [("title", False), ("id", False)],
            )
            == _INDEX_ABSENT
        )

    def test_migration_lagged_unique_constraint_is_unknown(self) -> None:
        """A ``UniqueConstraint`` naming an unresolvable field is uninspectable -> unknown."""
        assert (
            _index_coverage(
                _IdxChildUniqueConstraintMigrationLag,
                ["parent_id"],
                [("title", False), ("id", False)],
            )
            == _INDEX_UNKNOWN
        )

    def test_migration_lagged_unique_together_is_unknown(self) -> None:
        """A ``unique_together`` naming an unresolvable field is uninspectable -> unknown."""
        assert (
            _index_coverage(
                _IdxChildUniqueTogetherMigrationLag,
                ["parent_id"],
                [("title", False), ("id", False)],
            )
            == _INDEX_UNKNOWN
        )

    def test_unique_constraint_full_reverse_covers(self) -> None:
        """A unique btree (ascending) serves a FULL-reverse order via a backward scan."""
        assert (
            _index_coverage(
                _IdxChildUniqueConstraint,
                ["parent_id"],
                [("title", True), ("id", True)],
            )
            == _INDEX_COVERED
        )

    def test_non_btree_index_on_ordered_window_is_unknown(self) -> None:
        """A GIN index on the exact window columns does NOT cover an ORDER BY -> unknown.

        The false-``covered`` defect for non-B-tree indexes: the GIN access method
        cannot serve the multi-column ordering, so the covering-column shape must
        leave absence UNPROVEN (never suppress the advisory as if a real B-tree
        served the sort).
        """
        assert (
            _index_coverage(
                _IdxChildGin,
                ["parent_id"],
                [("title", False), ("id", False)],
            )
            == _INDEX_UNKNOWN
        )

    def test_non_btree_index_still_leaves_connector_only_window_covered(self) -> None:
        """The FK auto-index still serves a connector-only (orderless) window despite the GIN index."""
        assert _index_coverage(_IdxChildGin, ["parent_id"], []) == _INDEX_COVERED


class TestAdviseCompositeIndex:
    """``_advise_composite_index`` warns only under DEBUG, on PROVEN absence only."""

    @staticmethod
    def _join(column: str | None, content_type_column: str | None = None) -> SimpleNamespace:
        return SimpleNamespace(
            parent_join_column=column,
            content_type_column=content_type_column,
        )

    @staticmethod
    def _warnings(caplog) -> list:
        return [r for r in caplog.records if r.levelname == "WARNING"]

    @override_settings(DEBUG=True)
    def test_warns_when_no_covering_index(self, caplog) -> None:
        """A proven-missing composite index warns under DEBUG, naming model + columns."""
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(_IdxChildBare, self._join("parent_id"), ["title", "id"])
        warnings = self._warnings(caplog)
        assert len(warnings) == 1
        message = warnings[0].getMessage()
        assert "_IdxChildBare" in message
        assert "parent_id" in message

    @override_settings(DEBUG=False)
    def test_debug_off_does_not_warn(self, caplog) -> None:
        """With DEBUG off the advisory drops to ``debug`` level (no WARNING)."""
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(_IdxChildBare, self._join("parent_id"), ["title", "id"])
        assert not self._warnings(caplog)

    @override_settings(DEBUG=True)
    def test_covered_shape_is_silent(self, caplog) -> None:
        """A model whose composite index covers the shape emits nothing."""
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(_IdxChildComposite, self._join("parent_id"), ["title", "id"])
        assert not self._warnings(caplog)

    @override_settings(DEBUG=True)
    def test_fk_auto_index_only_shape_is_silent(self, caplog) -> None:
        """A single-column (connector-only) shape rides the FK index -> silent."""
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(_IdxChildBare, self._join("parent_id"), [])
        assert not self._warnings(caplog)

    @override_settings(DEBUG=True)
    def test_no_connector_returns_early(self, caplog) -> None:
        """No resolvable connector column -> nothing to advise, no crash."""
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(_IdxChildBare, self._join(None), ["title", "id"])
        assert not self._warnings(caplog)

    @override_settings(DEBUG=True)
    def test_expression_only_index_suppresses_warning(self, caplog) -> None:
        """An uninspectable expression index leaves absence UNPROVEN -> no warning.

        The P2 fail-soft contract: ``_index_coverage`` returns ``unknown`` for
        the expression-only model, so the advisory - tested end to end here, not
        at the intermediate helper - must stay silent rather than emit a loud
        false positive.
        """
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(_IdxChildExpr, self._join("parent_id"), ["title", "id"])
        assert not self._warnings(caplog)

    @override_settings(DEBUG=True)
    def test_mixed_direction_exact_cover_is_silent(self, caplog) -> None:
        """``title ASC, id DESC`` served by an index on ``(parent, title, -id)`` -> silent."""
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(_IdxChildMixed, self._join("parent_id"), ["title", "-id"])
        assert not self._warnings(caplog)

    @override_settings(DEBUG=True)
    def test_full_reverse_cover_is_silent(self, caplog) -> None:
        """``title ASC, id ASC`` served by the FULL reverse index ``(parent, -title, -id)``."""
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(_IdxChildReversed, self._join("parent_id"), ["title", "id"])
        assert not self._warnings(caplog)

    @override_settings(DEBUG=True)
    def test_partial_direction_flip_still_warns(self, caplog) -> None:
        """A partial flip cannot be served without a sort, so the advisory still warns.

        The index ``(parent, title, -id)`` serves neither ``title ASC, id ASC``
        nor its full reverse ``title DESC, id DESC``; the pre-fix name-only
        comparison wrongly declared it covered.
        """
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(_IdxChildMixed, self._join("parent_id"), ["title", "id"])
        warnings = self._warnings(caplog)
        assert len(warnings) == 1
        # The requested order is ascending; the recommendation names it plainly.
        assert "(parent_id, title, id)" in warnings[0].getMessage()

    @override_settings(DEBUG=True)
    def test_descending_order_annotates_desc_in_recommendation(self, caplog) -> None:
        """A descending order column is rendered ``DESC`` in the recommended shape."""
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(_IdxChildBare, self._join("parent_id"), ["title", "-id"])
        warnings = self._warnings(caplog)
        assert len(warnings) == 1
        assert "id DESC" in warnings[0].getMessage()

    @override_settings(DEBUG=True)
    def test_generic_relation_recommends_content_type_prefix(self, caplog) -> None:
        """A ``GenericRelation`` window recommends ``(content_type_id, object_id, ...)``.

        The join descriptor contributes ``content_type_column`` ahead of the
        ``object_id`` connector, so the advisory's recommended prefix leads with
        the morph column - the ``(content_type, object_id)`` model index does not
        cover the ``id`` order tail, so absence is proven and it warns.
        """
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        join = classify_relation_join(Branch._meta.get_field("tags"))
        content_type_attname = TaggedItem._meta.get_field("content_type").attname
        object_id_attname = TaggedItem._meta.get_field("object_id").attname
        _advise_composite_index(TaggedItem, join, ["id"])
        warnings = self._warnings(caplog)
        assert len(warnings) == 1
        message = warnings[0].getMessage()
        assert content_type_attname in message
        # The morph column leads the object_id connector in the recommended shape.
        assert message.index(content_type_attname) < message.index(object_id_attname)

    @override_settings(DEBUG=True)
    def test_expression_order_is_silent(self, caplog) -> None:
        """An expression order term (``Lower("title")``) keeps the advisory SILENT.

        The P2 fix: the effective order ``(Lower("title"), "id")`` is only
        partially understood, so ``_concrete_order_terms`` returns ``None`` and
        the advisory must neither warn nor claim coverage from the ``id`` suffix.
        Before the fix the expression was dropped and ``(parent_id, id)`` was
        wrongly recommended as the serving index.
        """
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(_IdxChildBare, self._join("parent_id"), [Lower("title"), "id"])
        assert not self._warnings(caplog)

    @override_settings(DEBUG=True)
    def test_related_span_order_is_silent(self, caplog) -> None:
        """A related-span order term (``parent__title``) keeps the advisory SILENT.

        Same P2 fail-soft as the expression case: a ``__``-spanning term is not a
        local concrete column, so the SQL order is only partially understood and
        no coverage claim (nor a suffix-only ``(parent_id, id)`` recommendation)
        may be made for this plan shape.
        """
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(_IdxChildBare, self._join("parent_id"), ["parent__title", "id"])
        assert not self._warnings(caplog)

    @override_settings(DEBUG=True)
    def test_nulls_placement_order_is_silent(self, caplog) -> None:
        """An explicit ``NULLS FIRST`` order term keeps the advisory SILENT (P2-2).

        ``title ASC NULLS FIRST`` is not index-provable, so the order is UNKNOWN
        and the advisory neither warns nor declares ``(parent_id, title, id)``
        covered - the false-``covered`` result the pre-fix name-only reduction hit.
        """
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(
            _IdxChildComposite,
            self._join("parent_id"),
            [models.F("title").asc(nulls_first=True), "id"],
        )
        assert not self._warnings(caplog)

    @override_settings(DEBUG=True)
    def test_equality_column_in_order_head_is_stripped_and_covered(self, caplog) -> None:
        """An order LED by the equality column is served by ``(parent_id, title, id)`` (P2-3).

        The window makes ``parent_id`` constant per partition, so ordering by
        ``parent_id, title, id`` is effectively ``title, id`` within a partition.
        The pre-fix code compared against ``(parent_id, parent_id, title, id)``,
        falsely reported the real index absent, and recommended a duplicated
        column; stripping the equality term makes the composite index cover it.
        """
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(
            _IdxChildComposite,
            self._join("parent_id"),
            ["parent_id", "title", "id"],
        )
        assert not self._warnings(caplog)

    @override_settings(DEBUG=True)
    def test_equality_column_in_order_middle_is_stripped_and_covered(self, caplog) -> None:
        """The equality column mid-order is stripped too (constant within the partition)."""
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(
            _IdxChildComposite,
            self._join("parent_id"),
            ["title", "parent_id", "id"],
        )
        assert not self._warnings(caplog)

    @override_settings(DEBUG=True)
    def test_unique_constraint_cover_is_silent(self, caplog) -> None:
        """An exact composite ``UniqueConstraint`` covers the window -> no duplicate warning (P2-3)."""
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(
            _IdxChildUniqueConstraint,
            self._join("parent_id"),
            ["title", "id"],
        )
        assert not self._warnings(caplog)

    @override_settings(DEBUG=True)
    def test_unique_together_cover_is_silent(self, caplog) -> None:
        """Legacy ``unique_together`` covering the window is silent."""
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(_IdxChildUniqueTogether, self._join("parent_id"), ["title", "id"])
        assert not self._warnings(caplog)

    @override_settings(DEBUG=True)
    def test_partial_index_only_is_silent(self, caplog) -> None:
        """A model whose only exact-column index is PARTIAL leaves absence unproven -> silent (P2-3)."""
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(_IdxChildPartial, self._join("parent_id"), ["title", "id"])
        assert not self._warnings(caplog)

    @override_settings(DEBUG=True)
    def test_repeated_plan_shape_warns_once(self, caplog) -> None:
        """The SAME plan shape rebuilt every request warns at most once (P3 dedup).

        A request-scoped plan (custom ``get_queryset``) is excluded from the
        cross-request plan cache, so ``plan_connection_relation`` re-runs the
        advisory each request; the bounded dedup collapses the repeats.
        """
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        for _ in range(3):
            _advise_composite_index(_IdxChildBare, self._join("parent_id"), ["title", "id"])
        assert len(self._warnings(caplog)) == 1

    @override_settings(DEBUG=True)
    def test_dedup_does_not_hide_different_shapes(self, caplog) -> None:
        """Genuinely different plan shapes each still warn once - the dedup never over-collapses."""
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        # Same model + connector, but different order terms -> a distinct shape.
        _advise_composite_index(_IdxChildBare, self._join("parent_id"), ["title", "id"])
        _advise_composite_index(_IdxChildBare, self._join("parent_id"), ["title", "-id"])
        assert len(self._warnings(caplog)) == 2

    @override_settings(DEBUG=True)
    def test_clear_dedup_re_enables_warning(self, caplog) -> None:
        """The reset seam lets one shape warn again (mirrors module-cache clears)."""
        caplog.set_level("WARNING", logger=optimizer_logger.name)
        _advise_composite_index(_IdxChildBare, self._join("parent_id"), ["title", "id"])
        clear_index_advisory_dedup()
        _advise_composite_index(_IdxChildBare, self._join("parent_id"), ["title", "id"])
        assert len(self._warnings(caplog)) == 2

    def test_bounded_dedup_evicts_least_recently_used_past_cap(self, monkeypatch) -> None:
        """The dedup LRU is BOUNDED: a shape past the cap evicts the least-recently-used.

        Exercises ``_index_advisory_already_emitted`` directly under a tiny cap so
        a long-lived process with a pathological variety of plan shapes cannot
        grow memory without limit; eviction only lets a long-cold advisory
        re-warn, never a wrong one.
        """
        from django_strawberry_framework.optimizer import nested_planner

        monkeypatch.setattr(nested_planner, "_MAX_INDEX_ADVISORY_KEYS", 2)
        emitted = nested_planner._index_advisory_already_emitted
        a = ("tests.A", ("p_id",), (("x", False),))
        b = ("tests.B", ("p_id",), (("x", False),))
        c = ("tests.C", ("p_id",), (("x", False),))
        assert emitted(a) is False  # first sight of A -> record, emit
        assert emitted(b) is False  # first sight of B -> record, emit
        assert emitted(a) is True  # A already present -> suppressed AND promoted (LRU recency)
        assert emitted(c) is False  # C overflows cap 2 -> B (the least-recently-used) evicted
        assert emitted(a) is True  # A survived: promotion protected it from the eviction
        assert (
            emitted(b) is False
        )  # B was the evicted LRU -> re-emits (bounded, not silent forever)


@pytest.mark.django_db
class TestAdvisoryDeferredUntilWindowAccepted:
    """P3-2: the field-static advisory fires only after a strategy ACCEPTS a window.

    A public consumer strategy may refuse every window (the connection then falls
    back per-parent); advising a composite WINDOW index for a backend that never
    runs is confusing under strictness, so the advisory is deferred into the
    per-window loop and latched to fire at most once, only after the first
    acceptance. Driven through an in-process schema (the faithful path) rather
    than the planner internals - ``Book`` has no index covering the shelf window,
    so the accepting run's warning is what proves the refusing run's silence is
    the deferral, not a covering index.
    """

    _QUERY = "{ shelves { code booksConnection(first: 2) { edges { node { title } } } } }"

    class _RefuseEveryWindow:
        name = "refuse-all"

        def plan(self, request, plan):
            return False

    @staticmethod
    def _warnings(caplog) -> list:
        return [r for r in caplog.records if r.levelname == "WARNING"]

    @staticmethod
    def _reset_type_caches() -> None:
        from django_strawberry_framework.connection import _connection_type_cache
        from django_strawberry_framework.registry import registry

        registry.clear()
        _connection_type_cache.clear()
        clear_index_advisory_dedup()

    @pytest.fixture(autouse=True)
    def _isolate_registry(self):
        """Clear the global registry / connection cache around this DB test.

        The test declares function-scope ``DjangoType`` classes; without isolation
        they would leak into other modules' identity checks (the recurring
        schema-registry cross-test pollution class).
        """
        self._reset_type_caches()
        yield
        self._reset_type_caches()

    @staticmethod
    def _shelf_books_schema(strategy):
        """A ``shelves { booksConnection }`` schema running ``strategy``."""
        import strawberry
        from apps.library.models import Book, Shelf
        from strawberry import relay

        from django_strawberry_framework import (
            DjangoOptimizerExtension,
            DjangoType,
            finalize_django_types,
            strawberry_config,
        )

        class BookNode(DjangoType):
            class Meta:
                model = Book
                fields = ("id", "title")
                interfaces = (relay.Node,)

        class ShelfNode(DjangoType):
            class Meta:
                model = Shelf
                fields = ("id", "code", "books")
                interfaces = (relay.Node,)

        @strawberry.type
        class Query:
            @strawberry.field
            def shelves(self) -> list[ShelfNode]:
                return Shelf.objects.order_by("id")

        finalize_django_types()
        ext = DjangoOptimizerExtension(nested_connection_strategy=strategy)
        return strawberry.Schema(
            query=Query,
            config=strawberry_config(),
            extensions=[lambda: ext],
        )

    @override_settings(DEBUG=True)
    def test_refusing_strategy_emits_no_advisory_but_windowed_does(self, caplog) -> None:
        """A strategy that refuses every window advises no index; windowed advises one."""
        from apps.library.models import Book, Branch, Shelf

        shelf = Shelf.objects.create(code="A", branch=Branch.objects.create(name="c"))
        for index in range(3):
            Book.objects.create(title=f"t{index}", shelf=shelf)
        caplog.set_level("WARNING", logger=optimizer_logger.name)

        # Refuses every window -> no window planned -> per-parent fallback, and NO
        # advisory (the P3-2 deferral): the page still resolves correctly.
        self._reset_type_caches()
        refused = self._shelf_books_schema(self._RefuseEveryWindow()).execute_sync(self._QUERY)
        assert refused.errors is None, refused.errors
        titles = [
            edge["node"]["title"]
            for edge in refused.data["shelves"][0]["booksConnection"]["edges"]
        ]
        assert titles == ["t0", "t1"]
        assert not self._warnings(caplog)

        # The SAME model/shape under the accepting windowed strategy DOES warn,
        # proving the silence above is the deferral, not a covering index.
        caplog.clear()
        self._reset_type_caches()
        accepted = self._shelf_books_schema("windowed").execute_sync(self._QUERY)
        assert accepted.errors is None, accepted.errors
        assert self._warnings(caplog)
