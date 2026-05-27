"""End-to-end coverage models for the package's scalar converter table.

Each field on ``ScalarSpecimen`` exercises a single entry from
``django_strawberry_framework/types/converters.py::SCALAR_MAP`` against a live
``/graphql/`` request, so the wire format of every non-``int`` / non-``str``
scalar conversion is pinned by an HTTP test rather than only by a package-
internal unit test. The trivial-collapse entries (everything mapped to plain
``int`` or plain ``str``) are covered transitively by every other example app.

``NullableScalarSpecimen`` mirrors ``ScalarSpecimen`` with every scalar field
nullable, exercising the other half of each converter row (the
``NON_NULL`` wrapper vs bare ``SCALAR`` shape) under the same live HTTP path.
A nullable forward FK ``partner`` links a ``NullableScalarSpecimen`` row to a
``ScalarSpecimen``, exposing both the cross-model FK shape and the reverse
relation (``ScalarSpecimen.nullable_partners``) — distinct from the intra-
model ``parent`` / ``children`` self-FK on ``ScalarSpecimen``. The two
models also let consumers compose richer example queries that span both
all-required and all-nullable shapes in one round-trip.

``ScalarSpecimenTag`` is the substrate for the O6 ``Prefetch``-downgrade
behavior: its companion ``ScalarSpecimenTagType`` declares a custom
``get_queryset()`` classmethod that filters to ``active=True``. A nullable
forward FK from ``ScalarSpecimen.tag`` points at it. Selecting
``tag { ... }`` from a query against ``allScalarSpecimens`` exercises the
optimizer's downgrade rule: a target type with custom ``get_queryset``
must be planned as ``Prefetch(qs)`` rather than ``select_related`` so the
consumer's filter survives — the resulting query shape is two SQL
statements (root SELECT + filtered tag SELECT), with the inactive-tag
rows resolving to ``null`` on the source-side specimen.

``ArrayField`` and ``HStoreField`` are deliberately absent — both are
PostgreSQL-only and the fakeshop runs on SQLite. Their converter entries stay
covered by ``tests/`` against package-internal fixtures.
"""

from decimal import Decimal

from django.db import models


class ScalarSpecimenTag(models.Model):
    """Tag referenced by ``ScalarSpecimen.tag``; substrate for the O6 downgrade rule.

    The companion ``ScalarSpecimenTagType`` declares a custom
    ``get_queryset()`` classmethod that filters to ``active=True``. The
    optimizer's O6 rule requires that any forward FK whose target type
    declares ``get_queryset`` be planned as ``Prefetch(qs)`` rather than
    ``select_related`` so the consumer's filter survives end-to-end —
    visible in the live test by an inactive tag resolving to ``null`` on
    the source specimen.
    """

    label = models.TextField(unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.label


class ScalarSpecimen(models.Model):
    """One row per "exercise this converter table entry end-to-end" case.

    Field names match the scalar they target (``flag`` -> ``BooleanField``,
    ``score`` -> ``FloatField``, ...) so the GraphQL response key reads as the
    target scalar in test assertions.
    """

    # ``label`` is a TextField rather than a generated identity column so each
    # row carries a human-readable handle inside the test response (the live
    # HTTP test pins each field's wire format against this label).
    label = models.TextField(unique=True)
    flag = models.BooleanField(default=False)
    score = models.FloatField(default=0.0)
    price = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        default=Decimal("0.0000"),
    )
    occurred_on = models.DateField()
    occurred_at = models.DateTimeField()
    occurred_time = models.TimeField()
    payload = models.JSONField(default=dict)
    external_id = models.UUIDField()
    # Signed 64-bit; exercises the ``BigIntegerField -> BigInt`` converter
    # entry directly (the library app's ``Patron.lifetime_fines_cents`` hits
    # the same entry; both stay because the scalar coverage app is the place
    # that pins every entry in one query).
    signed_big = models.BigIntegerField(default=0)
    # Unsigned 64-bit; exercises the ``PositiveBigIntegerField -> BigInt``
    # converter entry. Wire scalar is the same ``BigInt`` as the signed entry
    # but the converter table row is distinct.
    unsigned_big = models.PositiveBigIntegerField(default=0)
    # Self-referential FK. Lets the example exercise nullable-FK selection,
    # reverse-FK (``children``) traversal, and recursive
    # ``select_related`` / ``prefetch_related`` planning against a model
    # whose relation target is itself. Distinct from the library app, where
    # every relation crosses a model boundary.
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
    )
    # Forward FK to a target whose ``DjangoType`` declares a custom
    # ``get_queryset()``. Triggers the optimizer's O6 ``Prefetch``-
    # downgrade rule: forward-FK selection through ``tag`` must NOT use
    # ``select_related`` (which would JOIN raw, bypassing the consumer's
    # ``active=True`` filter), and the planner must record a
    # ``Prefetch(queryset=...)`` instead. ``on_delete=SET_NULL`` so
    # detaching a tag survives the cascade.
    tag = models.ForeignKey(
        ScalarSpecimenTag,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tagged_specimens",
    )

    def __str__(self):
        return self.label


class NullableScalarSpecimen(models.Model):
    """All-nullable mirror of ``ScalarSpecimen``.

    Every scalar field is ``null=True, blank=True`` so the nullable branch of
    each converter row in
    ``django_strawberry_framework/types/converters.py::SCALAR_MAP`` is
    exercised over a live ``/graphql/`` request. ``partner`` is a nullable
    cross-model FK to ``ScalarSpecimen`` (``on_delete=SET_NULL``) — distinct
    from the intra-model self-FK on ``ScalarSpecimen.parent``, and the only
    place in the example tree that exercises ``SET_NULL`` ondelete planning
    under the optimizer.
    """

    label = models.TextField(unique=True, null=True, blank=True)
    flag = models.BooleanField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    price = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True,
    )
    occurred_on = models.DateField(null=True, blank=True)
    occurred_at = models.DateTimeField(null=True, blank=True)
    occurred_time = models.TimeField(null=True, blank=True)
    payload = models.JSONField(null=True, blank=True)
    external_id = models.UUIDField(null=True, blank=True)
    signed_big = models.BigIntegerField(null=True, blank=True)
    unsigned_big = models.PositiveBigIntegerField(null=True, blank=True)
    # Cross-model link: a ``NullableScalarSpecimen`` may point at one
    # ``ScalarSpecimen``. ``SET_NULL`` so deleting a partner detaches the
    # row instead of cascading — the only ``SET_NULL`` ondelete in the
    # example tree.
    partner = models.ForeignKey(
        "scalars.ScalarSpecimen",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="nullable_partners",
    )

    def __str__(self):
        return self.label or f"NullableScalarSpecimen#{self.pk}"
