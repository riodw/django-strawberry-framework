"""Shared TEST-ONLY composite-primary-key relation fixture models.

These ``Rp*`` models carry a ``CompositePrimaryKey`` parent with a reverse
to-many, a relation shape the fakeshop example apps do not carry as
first-class models. They are defined here ONCE so every consumer imports the
same classes.

Each model is a plain ``django.db.models.Model`` with
``class Meta: app_label = "products"`` and ``managed = False``. The
``app_label`` MUST name an installed app so Django wires the reverse
relations into ``_meta.get_fields()``; ``managed = False`` keeps ``migrate``
and the test runner from ever creating or dropping their tables on their own.
Because nothing manages the tables, callers create and drop them on demand
with ``connection.schema_editor()`` via ``relation_fixture_tables``.

None of these classes is wrapped in a Strawberry ``DjangoType``; they must
never enter any GraphQL schema. The ``Rp`` prefix keeps the class and table
names distinct from the inline test models declared elsewhere in the suite.
"""

import contextlib

from django.db import models


class RpCompositeParent(models.Model):
    """A composite-primary-key parent (``tenant_id`` + ``code``).

    Django's ``CompositePrimaryKey`` (supported on the >= 5.2.16 floor this repo
    targets) names the concrete member fields; instance ``pk`` reads back as a
    tuple in declaration order (e.g. ``(1, "X")``).

    This family models a composite-primary-key parent whose reverse to-many
    needs a ``ForeignObject`` child (Django refuses a plain ``ForeignKey`` to a
    ``CompositePrimaryKey`` target, ``fields.E347``), a shape fakeshop excludes
    because Relay finalization rejects composite pks, and it alone executes
    ``django_strawberry_framework/optimizer/predicates.py::correlated_inner_root``
    against a real composite-pk table.
    """

    tenant_id = models.IntegerField()
    code = models.CharField(max_length=32)
    pk = models.CompositePrimaryKey("tenant_id", "code")
    label = models.CharField(max_length=64)

    class Meta:
        app_label = "products"
        managed = False


class RpCompositeChild(models.Model):
    """A child of the composite-pk parent, giving a reverse ``children`` hop.

    Django (every version on this repo's >= 5.2.16 floor) refuses a plain
    ``ForeignKey`` whose target has a ``CompositePrimaryKey`` -- system check
    ``fields.E347``, and ``schema_editor`` never emits the join column, so the
    relation is dead at runtime. The supported way to bind on a multi-column
    key is ``ForeignObject`` with ``from_fields`` / ``to_fields``: it is a
    virtual relation over the two concrete carrier columns
    (``parent_tenant_id`` / ``parent_code``) here, and it still yields the
    forward ``parent`` accessor and the reverse ``RpCompositeParent.children``
    to-many the later composite-pk correlation-execution tests rely on.
    Assigning ``parent=<instance>`` populates both carrier columns.
    """

    parent_tenant_id = models.IntegerField()
    parent_code = models.CharField(max_length=32)
    name = models.CharField(max_length=64)
    parent = models.ForeignObject(
        RpCompositeParent,
        on_delete=models.CASCADE,
        from_fields=["parent_tenant_id", "parent_code"],
        to_fields=["tenant_id", "code"],
        related_name="children",
    )

    class Meta:
        app_label = "products"
        managed = False


@contextlib.contextmanager
def relation_fixture_tables(connection):
    """Create the ``Rp*`` fixture tables via ``schema_editor``; drop on exit.

    The models are ``managed = False``, so their tables never exist until a
    caller materializes them. This context manager creates both in FK
    dependency order and deletes them in reverse on exit (including on
    error), leaving no residue in the test database.

    Callers must run under ``@pytest.mark.django_db(transaction=True)`` (the
    SQLite schema editor refuses to run inside the plain ``django_db`` atomic
    wrapper) and pass the test ``connection``
    (``from django.db import connection``).
    """
    models_in_order = [RpCompositeParent, RpCompositeChild]
    created: list[type[models.Model]] = []
    try:
        with connection.schema_editor() as editor:
            for m in models_in_order:
                editor.create_model(m)
                created.append(m)
        yield
    finally:
        # Drop whatever was successfully created, in reverse. Tracking
        # ``created`` (rather than ``models_in_order``) means a mid-list
        # ``create_model`` failure still tears down the earlier tables, so
        # the "no residue" guarantee holds even on partial construction.
        with connection.schema_editor() as editor:
            for m in reversed(created):
                editor.delete_model(m)
