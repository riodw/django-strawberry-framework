"""Managed models for library acceptance coverage."""

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models


class TaggedItem(models.Model):
    """A generic tag attached to any library-domain object."""

    tag = models.SlugField()
    content_type = models.ForeignKey(
        ContentType,
        related_name="library_tagged_items",
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "content_type",
                    "object_id",
                ],
                name="library_tagged_lookup_idx",
            ),
        ]

    def __str__(self):
        return self.tag


class Branch(models.Model):
    """A physical library branch that owns shelves."""

    name = models.TextField(unique=True)
    city = models.TextField(blank=True, default="")
    # Test substrate: package tests use this virtual relation to pin
    # GenericRelation support without exposing it in the public example schema.
    tags = GenericRelation(
        TaggedItem,
    )

    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"

    def __str__(self):
        return self.name


class ProxyBranch(Branch):
    """Proxy of ``Branch`` carrying a ``for_concrete_model=False`` generic relation.

    Substrate for the alias-late GenericRelation content-type morph under the
    NON-default ``for_concrete_model`` setting (``proxy_tags``, reached only by
    test-local types), and - through ``BranchNote.branch`` - the example's
    proxy-targeted relation target, exposed by
    ``apps/library/schema.py::ProxyBranchType``. ``proxy_tags`` filters ``TaggedItem`` rows by
    THIS proxy model's content type (``get_for_model(ProxyBranch,
    for_concrete_model=False)``), not ``Branch``'s concrete content type - so a
    generic connection over a ``ProxyBranch`` parent must resolve the proxy
    content type alias-late at fetch time. If planning ever re-baked a
    concrete-default content type (the removed plan-time lookup), rows seeded
    under the proxy content type would not match.
    """

    proxy_tags = GenericRelation(
        TaggedItem,
        for_concrete_model=False,
    )

    class Meta:
        proxy = True
        verbose_name = "Proxy branch"
        verbose_name_plural = "Proxy branches"


class BranchNote(models.Model):
    """A note whose branch foreign key is declared TO ``ProxyBranch``.

    One of the example's two relations declared to a PROXY model (the other is
    ``BranchSignage.branch``, whose proxy filters its default manager). A proxy
    reads its concrete model's table, so a prefetch child over ``Branch`` - and
    over ``ProxyBranch`` itself - belongs to this relation, while a child over
    any other table does not. Comparing a child against the DECLARED target
    instead of its concrete model cannot tell those cases apart, and every
    relation declared to a proxy is the shape that distinguishes them.
    """

    branch = models.ForeignKey(
        ProxyBranch,
        related_name="notes",
        on_delete=models.CASCADE,
    )
    body = models.TextField()

    def __str__(self):
        return self.body


class Shelf(models.Model):
    """A shelf inside a branch."""

    code = models.TextField()
    topic = models.TextField(blank=True, default="")
    branch = models.ForeignKey(
        Branch,
        related_name="shelves",
        on_delete=models.CASCADE,
    )
    # A shelf's additional/alternate branches. Exists to exercise a raw-pk M2M
    # relation input over a LIVE /graphql request: the M2M target is the non-Relay
    # ``BranchType`` primary, so the generated input is a raw pk list (not a
    # GlobalID), and the form/model mutations decode it through the same
    # visibility-scoped get_queryset path the single FK uses. Optional.
    alt_branches = models.ManyToManyField(
        Branch,
        blank=True,
        related_name="alt_shelves",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "branch",
                    "code",
                ],
                name="unique_shelf_code_per_branch",
            ),
        ]

    def __str__(self):
        return self.code


class Genre(models.Model):
    """A genre used to group books."""

    name = models.TextField(unique=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    """A shelved book with circulation state and genres."""

    class CirculationStatus(models.TextChoices):
        AVAILABLE = "available", "Available"
        CHECKED_OUT = "checked_out", "Checked out"
        REPAIR = "repair", "Repair"

    title = models.TextField()
    subtitle = models.TextField(blank=True, null=True)
    circulation_status = models.CharField(
        max_length=20,
        choices=CirculationStatus.choices,
        default=CirculationStatus.AVAILABLE,
    )
    shelf = models.ForeignKey(
        Shelf,
        related_name="books",
        on_delete=models.CASCADE,
    )
    genres = models.ManyToManyField(
        Genre,
        related_name="books",
    )
    # Genres a cataloguer archived the book under. Maintained by the catalogue
    # import, never by a client, so ``editable=False`` keeps it out of every
    # generated write input while the editable ``genres`` beside it stays in.
    archive_genres = models.ManyToManyField(
        Genre,
        related_name="+",
        editable=False,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "shelf",
                    "title",
                ],
                name="unique_book_title_per_shelf",
            ),
        ]

    def __str__(self):
        return self.title


class Patron(models.Model):
    """A library patron who can borrow books."""

    name = models.TextField(unique=True)
    email = models.TextField(blank=True, default="")
    # Signed 64-bit counter exercising the package's ``BigIntegerField -> BigInt``
    # converter entry end-to-end. Cents so values past 2^31-1 are realistic
    # for a long-running patron (>$21M in lifetime fines is plausible only as
    # a stress value, which is exactly the point - proves the wire format
    # survives values outside JSON's safe-integer range).
    lifetime_fines_cents = models.BigIntegerField(default=0)

    def __str__(self):
        return self.name


class MembershipCard(models.Model):
    """One-to-one membership card for a patron."""

    patron = models.OneToOneField(
        Patron,
        related_name="card",
        on_delete=models.CASCADE,
    )
    barcode = models.TextField(unique=True)

    def __str__(self):
        return self.barcode


class Periodical(models.Model):
    """A periodical whose issues paginate with keyset (value) cursors."""

    name = models.TextField(unique=True)

    def __str__(self):
        return self.name


class Issue(models.Model):
    """One issue of a periodical - the ``Meta.cursor_field`` acceptance substrate.

    ``number`` is the non-nullable ordering column ``IssueType.Meta.cursor_field``
    anchors (``("-number", "id")`` - newest-first with the pk tiebreak, the
    canonical keyset feed shape and the mixed-direction seek arm); numbers
    repeat ACROSS periodicals so the uniform value-position semantics of a
    nested ``after:`` cursor are observable. ``embargoed`` drives the
    ``IssueType.get_queryset`` visibility hook (the permission-aware
    cursor-decode coverage: a cursor minted under staff visibility replays
    for anonymous viewers without leaking embargoed rows).
    """

    periodical = models.ForeignKey(
        Periodical,
        related_name="issues",
        on_delete=models.CASCADE,
    )
    number = models.IntegerField()
    title = models.TextField()
    embargoed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "periodical",
                    "number",
                ],
                name="unique_issue_number_per_periodical",
            ),
        ]

    def __str__(self):
        return self.title


class LoanQuerySet(models.QuerySet):
    """A no-op project queryset used by the real ``Loan`` manager declaration."""


class Loan(models.Model):
    """A checkout record connecting a patron to a book."""

    # ``as_manager()`` keeps this project-only queryset out of migration state while
    # exercising the public Django manager shape through every real loan relation.
    objects = LoanQuerySet.as_manager()

    book = models.ForeignKey(
        Book,
        related_name="loans",
        on_delete=models.CASCADE,
    )
    patron = models.ForeignKey(
        Patron,
        related_name="loans",
        on_delete=models.CASCADE,
    )
    note = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "book",
                    "patron",
                ],
                name="unique_open_loan_per_book_patron",
            ),
        ]

    def __str__(self):
        return f"{self.book} to {self.patron}"


class Publisher(models.Model):
    """A publishing house whose wire identity is its stable house code.

    ``PublisherType`` declares ``house_code`` as the Relay ``NodeID``, so the
    id a client receives is built from a column a foreign key's stored key
    column does not carry. A forward key pointing here therefore keeps its
    join to the publisher row even when only the id is selected.
    """

    name = models.TextField(unique=True)
    house_code = models.TextField(unique=True)

    def __str__(self):
        return self.name


class Edition(models.Model):
    """One published edition of a work, keyed by its ISBN.

    The primary key is the text column ``isbn_13``: it is neither named
    ``id`` nor an integer, and its ``<word>_<digit>`` name does not survive
    the camel-case round trip, so a forward key to an edition has to resolve
    the real primary-key name before it can answer a key-only selection from
    the source row. ``isbn_10`` is the legacy ten-digit number, carrying the
    same digit boundary on a plain scalar; ``publisher_2`` is the second
    house on a jointly issued edition, carrying it on a relation.
    """

    isbn_13 = models.TextField(primary_key=True)
    isbn_10 = models.TextField(blank=True, default="")
    imprint = models.TextField(blank=True, default="")
    publisher = models.ForeignKey(
        Publisher,
        related_name="editions",
        on_delete=models.CASCADE,
    )
    publisher_2 = models.ForeignKey(
        Publisher,
        related_name="editions_2",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.isbn_13


class Printing(models.Model):
    """One press run of an edition.

    ``publisher_2`` is the second house of a jointly issued edition when that
    house commissioned the run, so a publisher's ``printings_2`` reverse
    relation carries a ``<word>_<digit>`` accessor that a nested connection
    over it must resolve before the window can be planned.
    """

    edition = models.ForeignKey(
        Edition,
        related_name="printings",
        on_delete=models.CASCADE,
    )
    publisher_2 = models.ForeignKey(
        Publisher,
        related_name="printings_2",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    run_size = models.IntegerField(default=0)

    class Meta:
        # The leading columns of a publisher's ``printings_2`` window, so each
        # page is served from the index instead of a per-partition sort.
        indexes = [
            models.Index(
                fields=[
                    "publisher_2",
                    "id",
                ],
                name="library_printing_window_idx",
            ),
        ]

    def __str__(self):
        return f"{self.edition_id} x{self.run_size}"


class PatronProfile(models.Model):
    """A patron's mailing details, keyed by the patron it extends.

    The primary key is the one-to-one key itself, so the field name
    (``patron``) and the column it loads (``patron_id``) differ and an id
    projection has to read the column. ``favorite_genre`` is stored by genre
    name rather than by genre key, so its column is not a related primary key
    and the join it needs cannot be skipped.
    """

    patron = models.OneToOneField(
        Patron,
        related_name="profile",
        on_delete=models.CASCADE,
        primary_key=True,
    )
    address_2 = models.TextField(blank=True, default="")
    postal_code = models.TextField(blank=True, default="")
    favorite_genre = models.ForeignKey(
        Genre,
        to_field="name",
        related_name="favoring_profiles",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"profile for {self.patron_id}"


class AnnotationManager(models.Manager):
    """Default manager collapsing the duplicate rows older imports left behind.

    ``distinct()`` on the base queryset cannot carry a per-parent window, so
    a nested connection over ``PatronProfile.annotations`` is left to the
    relation manager instead of being planned as one batched query.
    """

    def get_queryset(self):
        return super().get_queryset().distinct()


class Annotation(models.Model):
    """A patron's note on a page, read through their profile."""

    objects = AnnotationManager()

    profile = models.ForeignKey(
        PatronProfile,
        related_name="annotations",
        on_delete=models.CASCADE,
    )
    body = models.TextField()

    def __str__(self):
        return self.body


class Distributor(models.Model):
    """A trade distributor whose field names follow the camelCase feed it is mirrored from.

    Django keeps a mixed-case field name as written and names its column the
    same, and Strawberry publishes ``displayName`` unchanged, so reversing the
    published name gives ``display_name``, which names no field. The reverse
    relation ``consignmentItems`` carries the same shape on a relation.
    """

    displayName = models.TextField(unique=True)  # noqa: N815

    def __str__(self):
        return self.displayName


class Consignment(models.Model):
    """A batch of stock sent to a distributor through the mixed-case key ``distributorRef``.

    The key's column is ``distributorRef_id`` and its reverse accessor is the
    mixed-case ``consignmentItems``; neither name survives a reversal of its
    published spelling.
    """

    label = models.TextField()
    distributorRef = models.ForeignKey(  # noqa: N815
        Distributor,
        related_name="consignmentItems",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.label


class Venue(models.Model):
    """A place the library lends from, the root of a multi-table inheritance chain.

    ``LendingDesk`` extends it with its own table joined through the
    auto-created ``venue_ptr`` parent link, and ``SelfServeDesk`` extends that
    in turn, so a child row's inherited columns (``name``, ``opened_on``) live
    one or two joins away from its local ones. ``opened_on`` is the orderable
    parent column a child is sorted by.

    Its three reverse relations are declared WITHOUT ``related_name``
    (``RepairTicket.venue``, ``VenueBadge.venue``, ``VenueSponsor.venues``), so
    each is reached on an instance through Django's default accessor
    (``repairticket_set``, ``venuebadge``, ``venuesponsor_set``) while its query
    name is the bare model name. ``lead_ticket`` points back at ``RepairTicket``,
    closing a nullable foreign-key cycle between the two models.
    """

    name = models.TextField()
    opened_on = models.DateField(null=True, blank=True)
    lead_ticket = models.ForeignKey(
        "RepairTicket",
        related_name="+",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name


class LendingDesk(Venue):
    """A staffed desk: a ``Venue`` whose own table holds only its local columns."""

    window_count = models.IntegerField(default=0)


class SelfServeDesk(LendingDesk):
    """A kiosk desk, the third level of the ``Venue`` inheritance chain."""

    kiosk_code = models.TextField()


class OpenVenueManager(models.Manager):
    """Default manager keeping only venues that have opened."""

    def get_queryset(self):
        return super().get_queryset().filter(opened_on__isnull=False)


class OpenVenue(Venue):
    """Proxy of ``Venue`` whose default manager hides venues not yet opened.

    With ``LendingDesk`` beside it, the ``Venue`` table has both kinds of
    subclass: a proxy reading the same table and a concrete child with a table
    of its own.
    """

    objects = OpenVenueManager()

    class Meta:
        proxy = True


class RepairTicket(models.Model):
    """A maintenance ticket raised against a venue.

    ``venue`` declares no ``related_name``, so a venue reaches its tickets
    through the default ``repairticket_set`` accessor; the model declares no
    ``Meta.ordering``, so that accessor carries no default order.
    """

    code = models.TextField(unique=True)
    venue = models.ForeignKey(
        Venue,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.code


class VenueBadge(models.Model):
    """The accessibility badge a venue displays, one per venue.

    ``venue`` declares no ``related_name``, so the reverse accessor on a venue
    is the default ``venuebadge``.
    """

    code = models.TextField(unique=True)
    venue = models.OneToOneField(
        Venue,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.code


class VenueSponsor(models.Model):
    """A sponsor funding one or more venues.

    ``venues`` declares no ``related_name``, so a venue reaches its sponsors
    through the default ``venuesponsor_set`` accessor.
    """

    name = models.TextField(unique=True)
    venues = models.ManyToManyField(
        Venue,
        blank=True,
    )

    def __str__(self):
        return self.name


class VisibleBranchManager(models.Manager):
    """Default manager hiding branches that have no city on record."""

    def get_queryset(self):
        return super().get_queryset().exclude(city="")


class VisibleBranch(Branch):
    """Proxy of ``Branch`` whose default manager is its visibility policy.

    ``BranchSignage.branch`` is declared to this proxy. Django's forward
    descriptor loads the related row through ``_base_manager``, which does not
    apply this filter, so a signage row still reaches a city-less branch
    through ``signage.branch``; only a visibility cascade, which composes each
    edge target from its ``_default_manager``, hides that signage row.
    """

    objects = VisibleBranchManager()

    class Meta:
        proxy = True
        verbose_name = "Visible branch"
        verbose_name_plural = "Visible branches"


class BranchSignage(models.Model):
    """A sign mounted at a branch, declared against the filtering ``VisibleBranch`` proxy."""

    code = models.TextField(unique=True)
    branch = models.ForeignKey(
        VisibleBranch,
        related_name="signage",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.code


class CirculationDesk(models.Model):
    """The circulation counter of a branch, carrying every relation kind on one model.

    A forward key (``branch``), a forward one-to-one (``shelf``), a
    many-to-many (``genres``), a generic foreign key (``content_type`` /
    ``object_id`` / ``content_object``, the item currently on hold at the
    counter), a generic relation (``tags``), and two reverse relations with
    explicit names (``children`` from ``DeskShift``, ``profile`` from
    ``DeskProfile``). Only ``branch``, ``shelf`` and ``content_type`` are
    single-column forward relations; every other kind is reached through a join
    table, a pair of columns, or the other model's column.
    """

    name = models.TextField(unique=True)
    branch = models.ForeignKey(
        Branch,
        related_name="circulation_desks",
        on_delete=models.CASCADE,
    )
    shelf = models.OneToOneField(
        Shelf,
        related_name="circulation_desk",
        on_delete=models.CASCADE,
    )
    genres = models.ManyToManyField(
        Genre,
        related_name="circulation_desks",
        blank=True,
    )
    content_type = models.ForeignKey(
        ContentType,
        related_name="library_circulation_desks",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    tags = GenericRelation(
        TaggedItem,
    )

    def __str__(self):
        return self.name


class DeskShift(models.Model):
    """A staffed shift at a circulation desk, reached from the desk as ``children``."""

    name = models.TextField()
    desk = models.ForeignKey(
        CirculationDesk,
        related_name="children",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class DeskProfile(models.Model):
    """A circulation desk's service profile, reached from the desk as ``profile``."""

    code = models.TextField(unique=True)
    desk = models.OneToOneField(
        CirculationDesk,
        related_name="profile",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.code
