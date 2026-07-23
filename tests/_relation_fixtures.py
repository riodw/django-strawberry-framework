"""Shared TEST-ONLY relation fixture models for row-preserving-predicate work.

These ``Rp*`` models exercise two relation shapes that the fakeshop example
apps do not carry as first-class models: a forward ``to_field`` foreign key
whose join binds on a non-pk column (with its reverse to-many hop), and a
``CompositePrimaryKey`` parent with a reverse to-many. They are consumed by
later tasks (GlobalID ``to_field`` handling and composite-pk correlation
execution) and are defined here ONCE so every consumer imports the same
classes.

They follow this repo's established test-model idiom rather than living in a
Django app: each model is a plain ``django.db.models.Model`` with
``class Meta: app_label = "products"`` and ``managed = False``. The
``app_label`` MUST name an installed app so Django wires the reverse
relations into ``_meta.get_fields()``; ``managed = False`` keeps ``migrate``
and the test runner from ever creating or dropping their tables on their own.
Because nothing manages the tables, callers create and drop them on demand
with ``connection.schema_editor()`` via ``relation_fixture_tables`` -- see
``tests/test_relay_connection.py`` (the ``PlainAuthor`` / ``PlainBook``
reverse-FK fixture) and ``tests/test_lateral_pg_parity.py`` (the
``NaturalParent`` / ``NaturalChild`` / ``NaturalMembership`` lifecycle) for
the same pattern.

None of these classes is wrapped in a Strawberry ``DjangoType``; they must
never enter any GraphQL schema. The ``Rp`` prefix keeps the class and table
names distinct from the inline test models declared elsewhere in the suite.
"""

import contextlib

from django.db import models


class RpToFieldTarget(models.Model):
    """A ``to_field`` target whose auto pk deliberately differs from ``code``.

    ``code`` is the unique column that ``RpToFieldChild.target`` references,
    so the forward FK join and the reverse ``children`` hop both bind on
    ``code`` rather than on the auto pk -- the acceptance "matrix row 7"
    shape.
    """

    code = models.CharField(max_length=32, unique=True)
    label = models.CharField(max_length=64)

    class Meta:
        app_label = "products"
        managed = False


class RpToFieldChild(models.Model):
    """A child whose FK targets ``RpToFieldTarget.code`` (a non-pk column)."""

    target = models.ForeignKey(
        RpToFieldTarget,
        to_field="code",
        on_delete=models.CASCADE,
        related_name="children",
    )
    name = models.CharField(max_length=64)

    class Meta:
        app_label = "products"
        managed = False


class RpCompositeParent(models.Model):
    """A composite-primary-key parent (``tenant_id`` + ``code``).

    Django's ``CompositePrimaryKey`` (supported on the >= 5.2 floor this repo
    targets) names the concrete member fields; instance ``pk`` reads back as a
    tuple in declaration order (e.g. ``(1, "X")``).
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

    Django (every version on this repo's >= 5.2 floor) refuses a plain
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
    caller materializes them. This context manager creates all four in FK
    dependency order and deletes them in reverse on exit (including on
    error), leaving no residue in the test database.

    Callers must run under ``@pytest.mark.django_db(transaction=True)`` (the
    SQLite schema editor refuses to run inside the plain ``django_db`` atomic
    wrapper) and pass the test ``connection``
    (``from django.db import connection``).
    """
    models_in_order = [
        RpToFieldTarget,
        RpToFieldChild,
        RpCompositeParent,
        RpCompositeChild,
    ]
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
