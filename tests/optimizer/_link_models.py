"""Test-local models whose relations join on links other than a pk ``ForeignKey``.

Fakeshop carries no ``ForeignObject``, exposes no reverse relation over a
``to_field`` link (its one ``to_field`` FK, ``PatronProfile.favorite_genre``, is
reached only forward) and has no M2M through table keyed on ``to_field``, so
these models stand in for the link-column tests (optimizer projection, GlobalID
filter qualification, the generated forward relation over a multi-column link):
one parent keyed three ways, one child per link shape (the two-column link
twice, required and nullable), and a tag M2M whose through table joins both
sides on non-pk unique columns. ``app_label = "products"`` names an installed
app so Django wires the reverse relations into ``_meta.get_fields()``;
``managed = False`` keeps ``migrate`` from touching their tables, which
``link_fixture_tables`` creates, seeds and drops on demand. Unlike the ``Rp*``
models of ``tests/_relation_fixtures.py`` these may enter a test schema.
"""

import contextlib

from django.db import models


class LnkParent(models.Model):
    """A parent keyed three ways: pk, the ``(tenant, code)`` pair, and ``slug``."""

    tenant = models.IntegerField()
    code = models.TextField()
    slug = models.TextField(unique=True)
    label = models.TextField()
    tags = models.ManyToManyField(
        "LnkTag",
        through="LnkTagging",
        through_fields=("parent", "tag"),
        related_name="parents",
    )

    class Meta:
        app_label = "products"
        managed = False
        ordering = ["id"]
        unique_together = (("tenant", "code"),)


class LnkTag(models.Model):
    """An M2M target keyed by its non-pk unique ``code``."""

    code = models.TextField(unique=True)
    name = models.TextField()

    class Meta:
        app_label = "products"
        managed = False
        ordering = ["id"]


class LnkTagging(models.Model):
    """The ``LnkParent.tags`` through table: both foreign keys target non-pk columns.

    ``parent`` stores the parent's ``slug`` and ``tag`` the tag's ``code``, so an
    M2M hop in either direction matches through rows by a source-row column the
    primary key does not carry.
    """

    parent = models.ForeignKey(LnkParent, on_delete=models.CASCADE, to_field="slug")
    tag = models.ForeignKey(LnkTag, on_delete=models.CASCADE, to_field="code")

    class Meta:
        app_label = "products"
        managed = False
        ordering = ["id"]


class LnkPairChild(models.Model):
    """A child joined on two carrier columns (``p_tenant``, ``p_code``)."""

    p_tenant = models.IntegerField()
    p_code = models.TextField()
    name = models.TextField()
    parent = models.ForeignObject(
        LnkParent,
        on_delete=models.CASCADE,
        from_fields=["p_tenant", "p_code"],
        to_fields=["tenant", "code"],
        related_name="pair_children",
    )

    class Meta:
        app_label = "products"
        managed = False
        ordering = ["id"]


class LnkOptionalPairChild(models.Model):
    """A child whose two-column link may be absent: ``null=True`` over nullable carriers.

    ``related_name="+"`` keeps the link off ``LnkParent``'s field set, so the
    parent's declared and generated surfaces are those of the other children.
    """

    p_tenant = models.IntegerField(null=True)
    p_code = models.TextField(null=True)
    name = models.TextField()
    parent = models.ForeignObject(
        LnkParent,
        on_delete=models.CASCADE,
        from_fields=["p_tenant", "p_code"],
        to_fields=["tenant", "code"],
        null=True,
        related_name="+",
    )

    class Meta:
        app_label = "products"
        managed = False
        ordering = ["id"]


class LnkColumnChild(models.Model):
    """A child joined through a one-column ``ForeignObject`` on the parent pk."""

    p_id = models.IntegerField()
    name = models.TextField()
    parent = models.ForeignObject(
        LnkParent,
        on_delete=models.CASCADE,
        from_fields=["p_id"],
        to_fields=["id"],
        related_name="column_children",
    )

    class Meta:
        app_label = "products"
        managed = False
        ordering = ["id"]


class LnkSlugChild(models.Model):
    """A child whose ``ForeignKey`` targets the parent's non-pk ``slug``."""

    name = models.TextField()
    parent = models.ForeignKey(
        LnkParent,
        on_delete=models.CASCADE,
        to_field="slug",
        related_name="slug_children",
    )

    class Meta:
        app_label = "products"
        managed = False
        ordering = ["id"]


class LnkSlugObjectChild(models.Model):
    """A child joined through a one-column ``ForeignObject`` on the parent's non-pk ``slug``."""

    p_slug = models.TextField()
    name = models.TextField()
    parent = models.ForeignObject(
        LnkParent,
        on_delete=models.CASCADE,
        from_fields=["p_slug"],
        to_fields=["slug"],
        related_name="slug_object_children",
    )

    class Meta:
        app_label = "products"
        managed = False
        ordering = ["id"]


_MODELS = (
    LnkParent,
    LnkTag,
    LnkTagging,
    LnkPairChild,
    LnkOptionalPairChild,
    LnkColumnChild,
    LnkSlugChild,
    LnkSlugObjectChild,
)


@contextlib.contextmanager
def link_fixture_tables(connection):
    """Create the ``Lnk*`` tables and seed three parents; drop the tables on exit.

    Two parents share ``code="A"`` under different tenants, so a link that
    joined on ``code`` alone would mix their children; the third has none.
    Children per parent: ``("a1", "a2", "a3")``, ``("b1",)``, ``()``, once per
    child model. Tags per parent: ``("t1", "t2", "t3")``, ``("t1",)``, ``()``, so
    ``t1`` belongs to the first two parents and ``t2`` / ``t3`` to the first.
    ``LnkOptionalPairChild`` rows, in order: ``o1`` linked to the first parent,
    ``o2`` with both carriers ``NULL``, ``o3`` with only ``p_code`` ``NULL``, and
    ``o4`` whose carriers match no parent.
    Callers run under ``@pytest.mark.django_db(transaction=True)`` (the SQLite
    schema editor refuses the plain ``django_db`` atomic wrapper).
    """
    created: list[type[models.Model]] = []
    try:
        with connection.schema_editor() as editor:
            for model in _MODELS:
                editor.create_model(model)
                created.append(model)
        parents = (
            LnkParent.objects.create(tenant=1, code="A", slug="s-a", label="pa"),
            LnkParent.objects.create(tenant=2, code="A", slug="s-b", label="pb"),
            LnkParent.objects.create(tenant=1, code="B", slug="s-c", label="pc"),
        )
        for parent, names in zip(parents, (("a1", "a2", "a3"), ("b1",), ()), strict=True):
            for name in names:
                LnkPairChild.objects.create(p_tenant=parent.tenant, p_code=parent.code, name=name)
                LnkColumnChild.objects.create(p_id=parent.pk, name=name)
                LnkSlugChild.objects.create(parent=parent, name=name)
                LnkSlugObjectChild.objects.create(p_slug=parent.slug, name=name)
        tags = {
            name: LnkTag.objects.create(code=f"c-{name}", name=name) for name in ("t1", "t2", "t3")
        }
        for parent, names in zip(parents, (("t1", "t2", "t3"), ("t1",), ()), strict=True):
            for name in names:
                LnkTagging.objects.create(parent=parent, tag=tags[name])
        for name, tenant, code in (("o1", 1, "A"), ("o2", None, None), ("o3", 1, None)):
            LnkOptionalPairChild.objects.create(p_tenant=tenant, p_code=code, name=name)
        LnkOptionalPairChild.objects.create(p_tenant=9, p_code="Z", name="o4")
        yield
    finally:
        with connection.schema_editor() as editor:
            for model in reversed(created):
                editor.delete_model(model)
