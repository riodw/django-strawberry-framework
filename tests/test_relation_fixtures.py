"""Smoke tests proving the shared ``Rp*`` relation fixtures work end to end.

These pin the two fixture shapes that later tasks consume (GlobalID
``to_field`` handling and composite-pk correlation execution): a forward
``to_field`` FK plus its reverse to-many hop, and a ``CompositePrimaryKey``
parent with a reverse to-many. Each test runs under
``@pytest.mark.django_db(transaction=True)`` -- the SQLite schema editor
cannot run inside the plain ``django_db`` atomic wrapper -- and materializes
the ``managed = False`` tables via
``relation_fixture_tables(connection)`` -- the same manual ``schema_editor``
idiom the surrounding suite uses (``tests/test_relay_connection.py``,
``tests/test_lateral_pg_parity.py``).
"""

import pytest
from django.db import connection
from django.db.utils import DatabaseError

from tests._relation_fixtures import (
    RpCompositeChild,
    RpCompositeParent,
    RpToFieldChild,
    RpToFieldTarget,
    relation_fixture_tables,
)


@pytest.mark.django_db(transaction=True)
def test_to_field_pair_resolves_forward_and_reverse():
    """The ``to_field`` FK binds on ``code`` (not pk) both ways."""
    with relation_fixture_tables(connection):
        target = RpToFieldTarget.objects.create(code="ALPHA", label="A")
        # The whole point of the fixture: the auto pk is NOT the referenced
        # column, so a join on ``code`` cannot silently pass as a pk join.
        assert target.pk != target.code

        RpToFieldChild.objects.create(target=target, name="c1")
        # Reverse to-many across the non-pk ``code`` hop resolves.
        assert target.children.get().name == "c1"
        # Forward lookup by the related instance also binds on ``code``.
        assert RpToFieldChild.objects.filter(target=target).count() == 1


@pytest.mark.django_db(transaction=True)
def test_composite_pk_pair_round_trips():
    """The composite-pk parent exposes its tuple pk and a reverse to-many."""
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
    """After the context exits the tables are gone (managed = False, no residue)."""
    with relation_fixture_tables(connection):
        RpToFieldTarget.objects.create(code="ALPHA", label="A")

    # A missing relation raises a vendor-specific error -- ``OperationalError``
    # on SQLite, ``ProgrammingError`` (42P01) on PostgreSQL -- so assert their
    # common ``DatabaseError`` ancestor to stay green on both tiers.
    with pytest.raises(DatabaseError):
        RpToFieldTarget.objects.count()
