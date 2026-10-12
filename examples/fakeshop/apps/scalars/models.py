"""Models for scalar conversion, optimizer visibility, consumer overrides, and file/image uploads.

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
relation (``ScalarSpecimen.nullable_partners``) - distinct from the intra-
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
consumer's filter survives - the resulting query shape is two SQL
statements (root SELECT + filtered tag SELECT), with the inactive-tag
rows resolving to ``null`` on the source-side specimen.

``ArrayField`` and ``HStoreField`` are deliberately absent - both are
PostgreSQL-only and the fakeshop runs on SQLite. Their converter entries stay
covered by ``tests/`` against package-internal fixtures.

``MediaSpecimen`` carries a ``FileField`` and an ``ImageField`` so the spec-037
file/image converter rows are earned over a live ``/graphql/`` request (read =
``DjangoFileType`` / ``DjangoImageType`` output objects, write = the ``Upload``
scalar in the generated input). Unlike ``ArrayField`` / ``HStoreField`` these
ARE SQLite-compatible (they store the relative name as ``TEXT``), so they belong
here, not in synthetic package tests. The storage-backend fault-injection and
corrupt-image edges (which need mocking a non-filesystem backend) stay in
``tests/types/test_resolvers.py``.

``OverrideSpecimen`` is the substrate for the consumer-authored field-override
demonstration (spec-029): each of its columns is overridden a different way by
``OverriddenScalarSpecimenType`` (``apps/scalars/schema.py``), and its ``token``
column uses the deliberately-unsupported ``Base36Field`` so the consumer-
annotation escape hatch (a type the converter table cannot auto-map) is shown
live. ``manage.py inspect_django_type OverriddenScalarSpecimenType`` then prints
each field's true producing row in its converter column.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, TypeAlias, TypeVar

from django.db import models
from typing_extensions import override

if TYPE_CHECKING:
    from datetime import date, datetime, time
    from uuid import UUID

    from django.db.backends.base.base import BaseDatabaseWrapper
    from django.db.models.expressions import Combinable
    from django.db.models.fields.related_descriptors import RelatedManager

    _M = TypeVar("_M", bound=models.Model)

    # Each field's descriptor types as django-stubs declares them (set type, get type), spelled
    # out because the checker runs without the django-stubs mypy plugin that would infer them;
    # ``null=True`` adds ``None`` to both.
    _BigInt: TypeAlias = models.BigIntegerField[float | int | str | Combinable, int]
    _Bool: TypeAlias = models.BooleanField[bool | Combinable, bool]
    _Date: TypeAlias = models.DateField[str | date | Combinable, date]
    _DateTime: TypeAlias = models.DateTimeField[str | datetime | date | Combinable, datetime]
    _Decimal: TypeAlias = models.DecimalField[str | float | Decimal | Combinable, Decimal]
    _Float: TypeAlias = models.FloatField[float | int | str | Combinable, float]
    _Int: TypeAlias = models.IntegerField[float | int | str | Combinable, int]
    _NullBigInt: TypeAlias = models.BigIntegerField[
        float | int | str | Combinable | None,
        int | None,
    ]
    _NullBool: TypeAlias = models.BooleanField[bool | Combinable | None, bool | None]
    _NullDate: TypeAlias = models.DateField[str | date | Combinable | None, date | None]
    _NullDateTime: TypeAlias = models.DateTimeField[
        str | datetime | date | Combinable | None,
        datetime | None,
    ]
    _NullDecimal: TypeAlias = models.DecimalField[
        str | float | Decimal | Combinable | None,
        Decimal | None,
    ]
    _NullFK: TypeAlias = models.ForeignKey[_M | Combinable | None, _M | None]
    _NullFloat: TypeAlias = models.FloatField[float | int | str | Combinable | None, float | None]
    _NullPositiveBigInt: TypeAlias = models.PositiveBigIntegerField[
        float | int | str | Combinable | None,
        int | None,
    ]
    _NullText: TypeAlias = models.TextField[str | Combinable | None, str | None]
    _NullTime: TypeAlias = models.TimeField[str | time | datetime | Combinable | None, time | None]
    _NullUUID: TypeAlias = models.UUIDField[str | UUID | None, UUID | None]
    _PositiveBigInt: TypeAlias = models.PositiveBigIntegerField[
        float | int | str | Combinable,
        int,
    ]
    _Text: TypeAlias = models.TextField[str | Combinable, str]
    _Time: TypeAlias = models.TimeField[str | time | datetime | Combinable, time]
    _UUID: TypeAlias = models.UUIDField[str | UUID, UUID]
    # A JSON column decodes to whatever its decoder returns, and takes any value its encoder
    # accepts: django-stubs leaves both open, so neither side narrows past ``object``.
    _JSON: TypeAlias = models.JSONField[object, object]


class ScalarSpecimenTag(models.Model):
    """Tag referenced by ``ScalarSpecimen.tag``; substrate for the O6 downgrade rule.

    The companion ``ScalarSpecimenTagType`` declares a custom
    ``get_queryset()`` classmethod that filters to ``active=True``. The
    optimizer's O6 rule requires that any forward FK whose target type
    declares ``get_queryset`` be planned as ``Prefetch(qs)`` rather than
    ``select_related`` so the consumer's filter survives end-to-end -
    visible in the live test by an inactive tag resolving to ``null`` on
    the source specimen.
    """

    label: _Text = models.TextField(unique=True)
    active: _Bool = models.BooleanField(default=True)

    # Reverse accessor Django adds at class creation, declared for the type checker.
    tagged_specimens: RelatedManager[ScalarSpecimen]

    @override
    def __str__(self) -> str:
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
    label: _Text = models.TextField(unique=True)
    flag: _Bool = models.BooleanField(default=False)
    score: _Float = models.FloatField(default=0.0)
    price: _Decimal = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        default=Decimal("0.0000"),
    )
    occurred_on: _Date = models.DateField()
    occurred_at: _DateTime = models.DateTimeField()
    occurred_time: _Time = models.TimeField()
    payload: _JSON = models.JSONField(default=dict)
    external_id: _UUID = models.UUIDField()
    # Signed 64-bit; exercises the ``BigIntegerField -> BigInt`` converter
    # entry directly (the library app's ``Patron.lifetime_fines_cents`` hits
    # the same entry; both stay because the scalar coverage app is the place
    # that pins every entry in one query).
    signed_big: _BigInt = models.BigIntegerField(default=0)
    # Unsigned 64-bit; exercises the ``PositiveBigIntegerField -> BigInt``
    # converter entry. Wire scalar is the same ``BigInt`` as the signed entry
    # but the converter table row is distinct.
    unsigned_big: _PositiveBigInt = models.PositiveBigIntegerField(default=0)
    # Self-referential FK. Lets the example exercise nullable-FK selection,
    # reverse-FK (``children``) traversal, and recursive
    # ``select_related`` / ``prefetch_related`` planning against a model
    # whose relation target is itself. Distinct from the library app, where
    # every relation crosses a model boundary.
    parent: _NullFK[ScalarSpecimen] = models.ForeignKey(
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
    tag: _NullFK[ScalarSpecimenTag] = models.ForeignKey(
        ScalarSpecimenTag,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tagged_specimens",
    )

    # Key column Django adds beside ``parent``, declared for the type checker.
    parent_id: int | None
    # Reverse accessors Django adds at class creation, declared for the type checker.
    children: RelatedManager[ScalarSpecimen]
    nullable_partners: RelatedManager[NullableScalarSpecimen]

    @override
    def __str__(self) -> str:
        return self.label


class NullableScalarSpecimen(models.Model):
    """All-nullable mirror of ``ScalarSpecimen``.

    Every scalar field is ``null=True, blank=True`` so the nullable branch of
    each converter row in
    ``django_strawberry_framework/types/converters.py::SCALAR_MAP`` is
    exercised over a live ``/graphql/`` request. ``partner`` is a nullable
    cross-model FK to ``ScalarSpecimen`` (``on_delete=SET_NULL``) - distinct
    from the intra-model self-FK on ``ScalarSpecimen.parent``. Deleting the
    target clears ``partner_id`` and leaves this row in place, so a later
    query resolves ``partner`` as ``null`` with the source row still
    present; that end-to-end shape is pinned by
    ``test_query/test_scalars_api.py::test_scalars_set_null_ondelete_detaches_partner_in_http_query``.
    """

    label: _NullText = models.TextField(unique=True, null=True, blank=True)
    flag: _NullBool = models.BooleanField(null=True, blank=True)
    score: _NullFloat = models.FloatField(null=True, blank=True)
    price: _NullDecimal = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True,
    )
    occurred_on: _NullDate = models.DateField(null=True, blank=True)
    occurred_at: _NullDateTime = models.DateTimeField(null=True, blank=True)
    occurred_time: _NullTime = models.TimeField(null=True, blank=True)
    payload: _JSON = models.JSONField(null=True, blank=True)
    external_id: _NullUUID = models.UUIDField(null=True, blank=True)
    signed_big: _NullBigInt = models.BigIntegerField(null=True, blank=True)
    unsigned_big: _NullPositiveBigInt = models.PositiveBigIntegerField(null=True, blank=True)
    # Cross-model link: a ``NullableScalarSpecimen`` may point at one
    # ``ScalarSpecimen``. ``SET_NULL`` rather than ``CASCADE`` because every
    # field this model declares is ``null=True``: losing the target must
    # clear the FK, never delete the mirror row.
    partner: _NullFK[ScalarSpecimen] = models.ForeignKey(
        "scalars.ScalarSpecimen",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="nullable_partners",
    )
    # Key column Django adds beside ``partner``, declared for the type checker.
    partner_id: int | None

    @override
    def __str__(self) -> str:
        return self.label or f"NullableScalarSpecimen#{self.pk}"


class Base36Field(models.Field[str, str]):
    """A deliberately *unsupported* scalar column - no ``SCALAR_MAP`` entry.

    Subclasses ``models.Field`` directly (not ``CharField`` / ``TextField``), so
    ``django_strawberry_framework/types/converters.py::convert_scalar``'s
    ``type(field).__mro__`` walk finds no ``SCALAR_MAP`` match and auto-synthesis
    raises ``ConfigurationError``. It exists only to demonstrate the documented
    escape hatch: a consumer type annotation (``token: str`` on
    ``OverriddenScalarSpecimenType``) lets an otherwise-unconvertible column
    still surface in GraphQL. Stored as ``TEXT`` so SQLite round-trips it.
    """

    @override
    def db_type(
        self,
        connection: BaseDatabaseWrapper,
    ) -> str:
        return "text"


class MediaSpecimen(models.Model):
    """End-to-end coverage for the ``FileField`` / ``ImageField`` converter rows.

    Exercises the spec-037 file/image contract over a live ``/graphql/`` request
    rather than only package-internal synthetic schemas: on **read** a
    ``FileField`` converts to a structured ``DjangoFileType`` and an
    ``ImageField`` to ``DjangoImageType``; on **write** both columns map to
    Strawberry's ``Upload`` scalar in the generated ``MediaSpecimenInput``.
    ``FileField`` / ``ImageField`` are SQLite-compatible (they store the relative
    name as ``TEXT``), so this row earns its package coverage over HTTP like every
    other entry in this app instead of being deferred to synthetic tests.

    ``attachment`` and ``image`` are required (no ``null`` / ``blank``) **on
    purpose**: the live SDL then pins the default-nullable output-object contract
    (spec-037 Decision 4) - the generated ``attachment`` / ``image`` fields are
    nullable in the schema (`DjangoFileType` / `DjangoImageType`, no ``!``) even
    though the Django columns are required, because an empty / absent stored file
    resolves the whole object to ``null``. ``image`` reads ``width`` / ``height``
    through Pillow (a dev/test-only dependency, spec-037).

    The two optional columns beside them make the create input's requiredness
    rule observable one arm at a time: ``optional_attachment`` is optional only
    because it is ``blank=True``, and ``spare_image`` only because it is
    ``null=True`` (it is deliberately not ``blank``).
    """

    label: _Text = models.TextField(unique=True)
    attachment = models.FileField(upload_to="scalar_media/files/")
    image = models.ImageField(upload_to="scalar_media/images/")
    optional_attachment = models.FileField(upload_to="scalar_media/files/", blank=True)
    spare_image = models.ImageField(upload_to="scalar_media/images/", null=True)

    @override
    def __str__(self) -> str:
        return self.label


class OverrideSpecimen(models.Model):
    """Substrate for the consumer-authored field-override demonstration (spec-029).

    Four columns are each overridden a different way by
    ``OverriddenScalarSpecimenType`` so the four-corner consumer-override contract
    (annotation-only, assigned ``strawberry.field``, the ``annotation +
    strawberry.field`` overlap idiom, and an annotation escape hatch over the
    unsupported ``token``) is visible both at the GraphQL boundary and in
    ``inspect_django_type``'s converter column. The fifth column, ``note``, is the
    *declare-but-infer* corner: declared as ``note: auto`` so it appears as a class
    annotation alongside the four overrides while its GraphQL type is synthesized
    from the model exactly as bare ``Meta.fields`` selection would.
    """

    # Overridden by an assigned ``@strawberry.field`` resolver.
    label: _Text = models.TextField()
    # Overridden by an annotation-only ``quantity: float | None`` (the
    # ``IntegerField`` would auto-convert to ``Int!``).
    quantity: _Int = models.IntegerField(default=0)
    # Overridden by the ``score: int = strawberry.field(resolver=...)`` overlap.
    score: _Int = models.IntegerField(default=0)
    # Unsupported column; surfaced only via the consumer ``token: str`` annotation.
    token = Base36Field()
    # Declared as ``note: auto`` - selected and inferred (``TextField`` -> ``String!``)
    # rather than overridden, so the auto ``SCALAR_MAP`` converter still produces it.
    note: _Text = models.TextField(blank=True, default="")

    @override
    def __str__(self) -> str:
        return self.label
