"""Smoke tests proving the shared ``Rp*`` relation fixtures work end to end.

Fixture smoke for ``tests/_relation_fixtures.py``: ``managed = False`` table
create/drop via ``schema_editor`` and a ``CompositePrimaryKey`` parent with a
``ForeignObject`` reverse to-many. Composite-pk correlation execution imports
these classes; this file only proves the shared tables and accessors work
before those rows run.

A live ``/graphql/`` request cannot observe whether a test-only table exists,
whether instance ``pk`` is a tuple, or whether ``delete_model`` ran on context
exit: fakeshop ships no ``CompositePrimaryKey`` model (Relay finalization
rejects that pk shape), and ``tests/_relation_fixtures.py`` forbids wrapping
``Rp*`` in a ``DjangoType``. There is no live sibling in
``examples/fakeshop/test_query/``.

Each test runs under ``@pytest.mark.django_db(transaction=True)`` -- the
SQLite schema editor cannot run inside the plain ``django_db`` atomic
wrapper -- and materializes the tables via ``relation_fixture_tables``.
"""

import pytest
from django.db import connection
from django.db.utils import DatabaseError

from tests._relation_fixtures import (
    RpCompositeChild,
    RpCompositeParent,
    relation_fixture_tables,
)


@pytest.mark.django_db(transaction=True)
def test_composite_pk_pair_round_trips():
    """Fixture smoke: the composite-pk parent exposes its tuple pk and a reverse to-many.

    No live request can express this: fakeshop has no ``CompositePrimaryKey``
    model, and Relay finalization rejects that pk shape. Rungs 1-3 would wrap
    ``Rp*`` in GraphQL, which these models must never enter.
    """
    with relation_fixture_tables(connection):
        parent = RpCompositeParent.objects.create(tenant_id=1, code="X", label="P")
        # Django renders a CompositePrimaryKey instance's pk as a tuple in
        # declaration order.
        assert parent.pk == (1, "X")

        RpCompositeChild.objects.create(parent=parent, name="k1")
        assert parent.children.get().name == "k1"
        assert RpCompositeChild.objects.filter(parent=parent).count() == 1


@pytest.mark.django_db(transaction=True)
def test_fixture_tables_are_dropped_on_exit():
    """Fixture smoke: after the context exits the tables are gone (no residue).

    No live request can express this: ``schema_editor.delete_model`` is
    test-DB hygiene, not a GraphQL wire shape. Rungs 1-3 have nothing to post.
    """
    with relation_fixture_tables(connection):
        RpCompositeParent.objects.create(tenant_id=1, code="ALPHA", label="A")

    # A missing relation raises a vendor-specific error -- ``OperationalError``
    # on SQLite, ``ProgrammingError`` (42P01) on PostgreSQL -- so assert their
    # common ``DatabaseError`` ancestor to stay green on both tiers.
    with pytest.raises(DatabaseError):
        RpCompositeParent.objects.count()
