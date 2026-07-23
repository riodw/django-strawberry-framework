"""Relation utility tests for kinds, many-side detection, instance accessors, and package re-exports."""

from types import SimpleNamespace

import pytest
from apps.kanban.models import Decision
from apps.library.models import Book, Branch, Genre, Loan, Patron, TaggedItem
from django.core.exceptions import FieldDoesNotExist

from django_strawberry_framework.exceptions import (
    ConfigurationError,
    DjangoStrawberryFrameworkError,
    LookupValidationError,
    PathResolutionError,
)
from django_strawberry_framework.utils import (
    RelationKind,
    is_many_side_relation_kind,
    relation_kind,
)
from django_strawberry_framework.utils.relations import (
    ClassifiedPath,
    RelationPathHop,
    classify_path,
    instance_accessor,
    path_traverses_to_many,
    validate_lookup_expr,
)
from django_strawberry_framework.utils.relations import (
    RelationKind as _RelationKindSubmodule,
)
from django_strawberry_framework.utils.relations import (
    is_many_side_relation_kind as _is_many_side_relation_kind_submodule,
)
from django_strawberry_framework.utils.relations import (
    relation_kind as _relation_kind_submodule,
)


def test_relation_kind_classifies_many_to_many_as_many():
    field = SimpleNamespace(
        many_to_many=True,
        one_to_many=False,
        one_to_one=False,
        auto_created=False,
    )

    assert relation_kind(field) == "many"


def test_relation_kind_classifies_one_to_many_as_many():
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=True,
        one_to_one=False,
        auto_created=False,
    )

    assert relation_kind(field) == "many"


def test_relation_kind_classifies_generic_relation():
    """A ``GenericRelation``-shaped field classifies as ``"generic"`` before the fallback.

    Detected duck-typed by non-``None`` ``content_type_field_name`` /
    ``object_id_field_name`` slots, BEFORE the ``one_to_many`` ``"many"``
    fallback below.
    """
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=True,
        one_to_one=False,
        auto_created=False,
        content_type_field_name="content_type",
        object_id_field_name="object_id",
    )

    assert relation_kind(field) == "generic"


def test_relation_kind_none_valued_generic_slots_fall_back_to_many():
    """``None`` content-type / object-id slots (a plain ``FieldMeta``) are NOT generic.

    ``FieldMeta`` is a slotted dataclass that always carries the two slots
    defaulted to ``None``, so the detector reads ``getattr(...) is not None``,
    not ``hasattr`` - otherwise every ``FieldMeta`` snapshot would misclassify
    as ``"generic"``.
    """
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=True,
        one_to_one=False,
        auto_created=False,
        content_type_field_name=None,
        object_id_field_name=None,
    )

    assert relation_kind(field) == "many"


def test_relation_kind_generic_is_in_literal():
    """The ``RelationKind`` alias enumerates ``"generic"``."""
    import typing

    assert "generic" in typing.get_args(RelationKind)


def test_relation_kind_classifies_auto_created_one_to_many_as_reverse_many_to_one():
    """Reverse-FK descriptor (Django ``ManyToOneRel``): ``one_to_many`` + ``auto_created``."""
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=True,
        one_to_one=False,
        auto_created=True,
    )

    assert relation_kind(field) == "reverse_many_to_one"


def test_relation_kind_reverse_many_to_one_is_in_literal():
    """The ``RelationKind`` alias enumerates ``"reverse_many_to_one"``.

    ``tests/test_registry.py`` constructs a ``PendingRelation`` with this
    value against the typed ``relation_kind`` field; the alias must list
    it so the contract and the call sites agree.
    """
    import typing

    assert "reverse_many_to_one" in typing.get_args(RelationKind)


def test_utils_init_reexports_match_submodule():
    """``utils.relation_kind`` / ``utils.RelationKind`` re-export the submodule contract."""
    assert relation_kind is _relation_kind_submodule
    assert RelationKind is _RelationKindSubmodule
    assert is_many_side_relation_kind is _is_many_side_relation_kind_submodule


def test_is_many_side_relation_kind_matches_list_valued_shapes():
    assert is_many_side_relation_kind("many") is True
    assert is_many_side_relation_kind("reverse_many_to_one") is True
    assert is_many_side_relation_kind("generic") is True
    assert is_many_side_relation_kind("reverse_one_to_one") is False
    assert is_many_side_relation_kind("forward_single") is False
    assert is_many_side_relation_kind(None) is False


def test_relation_kind_classifies_auto_created_one_to_one_as_reverse():
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=False,
        one_to_one=True,
        auto_created=True,
        concrete=False,
    )

    assert relation_kind(field) == "reverse_one_to_one"


def test_relation_kind_classifies_forward_single_relations():
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=False,
        one_to_one=True,
        auto_created=False,
    )

    assert relation_kind(field) == "forward_single"


def test_relation_kind_classifies_concrete_auto_created_o2o_as_forward_single():
    """An auto-created MTI parent link is concrete and forward."""
    field = SimpleNamespace(
        many_to_many=False,
        one_to_many=False,
        one_to_one=True,
        auto_created=True,
        concrete=True,
    )

    assert relation_kind(field) == "forward_single"


def test_instance_accessor_uses_get_accessor_name_for_reverse_relations():
    """A reverse rel's instance attribute is ``get_accessor_name()``, not ``name``.

    For a reverse FK declared without ``related_name``, Django's
    ``ForeignObjectRel.name`` is the related QUERY name (``"book"``) while the
    instance attribute is ``"book_set"`` - the Round-4 S3 split.
    """
    rel = SimpleNamespace(name="book", get_accessor_name=lambda: "book_set")
    assert instance_accessor(rel) == "book_set"


def test_instance_accessor_falls_back_to_name_for_forward_fields():
    """Forward fields have no ``get_accessor_name``; ``name`` IS the attribute."""
    field = SimpleNamespace(name="genres")
    assert instance_accessor(field) == "genres"


def test_instance_accessor_prefers_precomputed_field_meta_slot():
    """A ``FieldMeta``-style ``accessor_name`` slot wins over any live lookup.

    ``FieldMeta`` cannot answer ``get_accessor_name()`` (it is a frozen
    snapshot), so the builders precompute the accessor into ``accessor_name``
    and this helper reads it first - the optimizer walker passes ``FieldMeta``
    values, not raw descriptors.
    """
    meta_like = SimpleNamespace(
        name="book",
        accessor_name="book_set",
        get_accessor_name=lambda: "WRONG-not-consulted",
    )
    assert instance_accessor(meta_like) == "book_set"


# ---------------------------------------------------------------------------
# classify_path: strict, immutable model-path classification.
# ---------------------------------------------------------------------------


def test_classify_path_local_scalar_has_no_hops():
    """A local column classifies to zero hops with the concrete field as terminal."""
    plan = classify_path(Book, "title")

    assert isinstance(plan, ClassifiedPath)
    assert plan.model is Book
    assert plan.path == "title"
    assert plan.hops == ()
    assert plan.terminal is Book._meta.get_field("title")
    assert plan.first_many_index is None
    assert plan.relation_chain == ()


def test_classify_path_forward_fk_chain_is_row_preserving():
    """A forward FK chain yields forward_single hops and no many boundary."""
    plan = classify_path(Book, "shelf__branch__name")

    assert [hop.segment for hop in plan.hops] == ["shelf", "branch"]
    assert [hop.kind for hop in plan.hops] == ["forward_single", "forward_single"]
    assert [hop.many_side for hop in plan.hops] == [False, False]
    from apps.library.models import Branch as _Branch
    from apps.library.models import Shelf as _Shelf

    assert [hop.target_model for hop in plan.hops] == [_Shelf, _Branch]
    assert plan.terminal is _Branch._meta.get_field("name")
    assert plan.first_many_index is None
    assert plan.relation_chain == ("shelf", "branch")


def test_classify_path_accepts_pk_alias_mid_and_tail():
    """``pk`` resolves to the model's pk field as a scalar terminal after a FK hop."""
    from apps.library.models import Shelf as _Shelf

    plan = classify_path(Book, "shelf__pk")

    assert [hop.segment for hop in plan.hops] == ["shelf"]
    assert plan.terminal is _Shelf._meta.pk
    assert plan.first_many_index is None
    assert plan.relation_chain == ("shelf",)

    deep = classify_path(Book, "shelf__branch__pk")
    assert deep.relation_chain == ("shelf", "branch")
    assert deep.terminal is Branch._meta.pk


def test_classify_path_reverse_fk_is_first_many():
    """A leading reverse FK is the first many-side boundary."""
    plan = classify_path(Book, "loans__note")

    (hop,) = plan.hops
    assert hop.segment == "loans"
    assert hop.kind == "reverse_many_to_one"
    assert hop.target_model is Loan
    assert hop.many_side is True
    assert plan.first_many_index == 0
    assert plan.terminal is Loan._meta.get_field("note")
    assert plan.relation_chain == ("loans",)


def test_classify_path_forward_m2m_is_first_many():
    """A forward M2M is a many-side hop even where its PathInfo expansion is mixed."""
    plan = classify_path(Book, "genres__name")

    (hop,) = plan.hops
    assert hop.segment == "genres"
    assert hop.kind == "many"
    assert hop.target_model is Genre
    assert hop.many_side is True
    assert plan.first_many_index == 0
    assert plan.terminal is Genre._meta.get_field("name")


def test_classify_path_reverse_m2m_is_first_many():
    """The reverse side of an M2M is also many-side."""
    plan = classify_path(Genre, "books__title")

    (hop,) = plan.hops
    assert hop.segment == "books"
    assert hop.kind == "many"
    assert hop.target_model is Book
    assert hop.many_side is True
    assert plan.first_many_index == 0


def test_classify_path_generic_relation_is_many_side():
    """A ``GenericRelation`` is a traversable many-side hop classified ``generic``."""
    plan = classify_path(Branch, "tags__tag")

    (hop,) = plan.hops
    assert hop.segment == "tags"
    assert hop.kind == "generic"
    assert hop.target_model is TaggedItem
    assert hop.many_side is True
    assert plan.first_many_index == 0
    assert plan.terminal is TaggedItem._meta.get_field("tag")


def test_classify_path_reverse_o2o_is_row_preserving():
    """A reverse O2O is single-valued: reverse_one_to_one, no many boundary."""
    plan = classify_path(Patron, "card__barcode")

    from apps.library.models import MembershipCard

    (hop,) = plan.hops
    assert hop.segment == "card"
    assert hop.kind == "reverse_one_to_one"
    assert hop.target_model is MembershipCard
    assert hop.many_side is False
    assert plan.first_many_index is None
    assert plan.terminal is MembershipCard._meta.get_field("barcode")


def test_classify_path_named_reverse_fk_behind_to_one_prefix():
    """The named Medtrics category: a reverse FK behind a to-one prefix.

    ``Loan.book -> Book.loans -> Loan.patron -> Patron.email`` contains NO
    ``ManyToManyField``; the row-multiplying hop is the mid-path reverse FK, so
    ``first_many_index`` MUST be 1, not 0.
    """
    plan = classify_path(Loan, "book__loans__patron__email")

    assert [hop.segment for hop in plan.hops] == ["book", "loans", "patron"]
    assert [hop.kind for hop in plan.hops] == [
        "forward_single",
        "reverse_many_to_one",
        "forward_single",
    ]
    assert [hop.many_side for hop in plan.hops] == [False, True, False]
    assert [hop.target_model for hop in plan.hops] == [Book, Loan, Patron]
    assert plan.terminal is Patron._meta.get_field("email")
    assert plan.first_many_index == 1
    assert plan.relation_chain == ("book", "loans", "patron")


def test_classify_path_relation_terminal_is_hop_and_terminal():
    """A relation reached at the final segment is both the last hop and the terminal."""
    plan = classify_path(Book, "genres")

    (hop,) = plan.hops
    genres_field = Book._meta.get_field("genres")
    assert hop.segment == "genres"
    assert hop.kind == "many"
    assert plan.terminal is genres_field
    assert plan.first_many_index == 0
    assert plan.relation_chain == ("genres",)


def test_classify_path_self_referential_forward_chain_is_row_preserving():
    """A self-FK forward chain of differing depth stays row-preserving."""
    one = classify_path(Decision, "supersedes__question")
    assert [hop.segment for hop in one.hops] == ["supersedes"]
    assert one.hops[0].kind == "forward_single"
    assert one.hops[0].target_model is Decision
    assert one.first_many_index is None

    two = classify_path(Decision, "supersedes__supersedes__question")
    assert [hop.segment for hop in two.hops] == ["supersedes", "supersedes"]
    assert [hop.target_model for hop in two.hops] == [Decision, Decision]
    assert two.first_many_index is None
    assert two.terminal is Decision._meta.get_field("question")


def test_classify_path_self_referential_reverse_fk_is_many():
    """The reverse side of a self-FK is a many-side hop."""
    plan = classify_path(Decision, "superseded_by_set__question")

    (hop,) = plan.hops
    assert hop.segment == "superseded_by_set"
    assert hop.kind == "reverse_many_to_one"
    assert hop.target_model is Decision
    assert hop.many_side is True
    assert plan.first_many_index == 0


def test_classify_path_unresolvable_segment_raises():
    """A missing leading segment raises with model, path, and segment named."""
    with pytest.raises(PathResolutionError) as excinfo:
        classify_path(Book, "nonexistent__name")

    err = excinfo.value
    assert err.segment == "nonexistent"
    assert err.field_path == "nonexistent__name"
    assert err.model is Book
    message = str(err)
    assert "library.Book" in message
    assert "nonexistent__name" in message
    assert "nonexistent" in message


def test_classify_path_garbage_tail_after_scalar_raises():
    """A scalar segment followed by more path components raises."""
    with pytest.raises(PathResolutionError) as excinfo:
        classify_path(Book, "title__nonsense")

    assert excinfo.value.segment == "title"
    assert "title__nonsense" in str(excinfo.value)


def test_classify_path_forward_gfk_traversal_raises():
    """A forward ``GenericForeignKey`` mid-path raises (no ``path_infos``)."""
    with pytest.raises(PathResolutionError) as excinfo:
        classify_path(TaggedItem, "content_object__x")

    assert excinfo.value.segment == "content_object"
    assert "library.TaggedItem" in str(excinfo.value)


def test_classify_path_bare_forward_gfk_raises():
    """A bare forward ``GenericForeignKey`` is neither scalar nor traversable."""
    with pytest.raises(PathResolutionError) as excinfo:
        classify_path(TaggedItem, "content_object")

    assert excinfo.value.segment == "content_object"


def test_classify_path_hidden_reverse_relation_raises():
    """A ``related_name='+'`` hidden reverse name is rejected by ``get_field``.

    No fakeshop model declares ``related_name='+'``; the resolution path is the
    same ``FieldDoesNotExist`` branch a missing name takes, proven above.
    """
    with pytest.raises(PathResolutionError):
        classify_path(Patron, "definitely_hidden_reverse")


def test_classify_path_empty_path_infos_relation_raises():
    """A relation exposing empty ``path_infos`` raises (defensive - no real field does).

    Stock Django relation descriptors always populate ``path_infos``; this pins
    the fail-closed branch with a minimal fake model whose ``get_field`` returns
    a traversable-looking relation with an empty ``path_infos``.
    """
    fake_field = SimpleNamespace(is_relation=True, path_infos=[])
    fake_model = SimpleNamespace(
        _meta=SimpleNamespace(get_field=lambda _segment: fake_field),
    )

    with pytest.raises(PathResolutionError) as excinfo:
        classify_path(fake_model, "rel")

    assert excinfo.value.segment == "rel"


def test_path_resolution_error_is_configuration_family():
    """``PathResolutionError`` is catchable as ConfigurationError and the base."""
    err = PathResolutionError(Book, "loans__x", "x")
    assert isinstance(err, ConfigurationError)
    assert isinstance(err, DjangoStrawberryFrameworkError)


def test_relation_path_hop_and_classified_path_are_frozen():
    """The plan records are immutable frozen dataclasses."""
    from dataclasses import FrozenInstanceError

    hop = RelationPathHop(segment="s", kind="many", target_model=Book, many_side=True)
    with pytest.raises(FrozenInstanceError):
        hop.segment = "other"  # type: ignore[misc]

    plan = classify_path(Book, "title")
    with pytest.raises(FrozenInstanceError):
        plan.path = "other"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("model", "path"),
    [
        (Book, "title"),
        (Book, "shelf__branch__name"),
        (Book, "shelf__pk"),
        (Book, "loans__note"),
        (Book, "genres__name"),
        (Genre, "books__title"),
        (Branch, "tags__tag"),
        (Patron, "card__barcode"),
        (Loan, "book__loans__patron__email"),
        (Decision, "supersedes__supersedes__question"),
        (Decision, "superseded_by_set__question"),
    ],
)
def test_classify_path_first_many_matches_django_oracle(model, path):
    """``first_many_index is not None`` matches Django's own duplicate oracle.

    ``lookup_spawns_duplicates`` is imported in the TEST ONLY - it must never
    appear in production code.
    """
    from django.contrib.admin.utils import lookup_spawns_duplicates

    spawns = classify_path(model, path).first_many_index is not None
    assert spawns == lookup_spawns_duplicates(model._meta, path)


# ---------------------------------------------------------------------------
# validate_lookup_expr: transform + lookup validation, separate from paths.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("lookup_expr", "lookup_name"),
    [
        ("icontains", "IContains"),
        ("exact", "Exact"),
        ("in", "In"),
        ("isnull", "IsNull"),
        ("gte", "GreaterThanOrEqual"),
    ],
)
def test_validate_lookup_expr_plain_lookups_on_scalar(lookup_expr, lookup_name):
    """A plain final lookup on a scalar terminal resolves to its lookup class."""
    terminal = Book._meta.get_field("title")
    resolved = validate_lookup_expr(terminal, lookup_expr)
    assert resolved.__name__ == lookup_name


def test_validate_lookup_expr_transform_chain_advances_output_field():
    """A ``date__year__gte`` chain validates through each transform's output field.

    ``Decision.created_date`` is a ``DateTimeField``: ``date`` -> ``DateField``,
    ``year`` -> ``IntegerField``, then ``gte`` resolves as the integer lookup.
    """
    terminal = Decision._meta.get_field("created_date")
    resolved = validate_lookup_expr(terminal, "date__year__gte")
    # The lookup is resolved against the year transform's IntegerField output.
    assert resolved.__name__ == "YearGte"


def test_validate_lookup_expr_trailing_transform_implies_exact():
    """A trailing transform (no final lookup) is accepted as ``transform + exact``.

    ``date`` on a ``DateTimeField`` is a transform, not a lookup; Django treats
    a lookup path ending on a transform as an implicit ``exact`` on the
    transform output, so validation returns the ``Exact`` lookup class.
    """
    terminal = Decision._meta.get_field("created_date")
    resolved = validate_lookup_expr(terminal, "date")
    assert resolved.__name__ == "Exact"


def test_validate_lookup_expr_invalid_final_lookup_raises():
    """An unknown final lookup on a valid terminal raises with message content."""
    terminal = Book._meta.get_field("title")
    with pytest.raises(LookupValidationError) as excinfo:
        validate_lookup_expr(terminal, "not_a_lookup")

    err = excinfo.value
    assert err.part == "not_a_lookup"
    assert err.lookup_expr == "not_a_lookup"
    assert err.terminal is terminal
    message = str(err)
    assert "not_a_lookup" in message
    assert "title" in message


def test_validate_lookup_expr_invalid_mid_chain_transform_raises():
    """An unresolvable non-final transform raises naming the offending part."""
    terminal = Decision._meta.get_field("created_date")
    with pytest.raises(LookupValidationError) as excinfo:
        validate_lookup_expr(terminal, "bogus__gte")

    assert excinfo.value.part == "bogus"
    assert "bogus__gte" in str(excinfo.value)


def test_validate_lookup_expr_trailing_transform_without_exact_support_raises():
    """A final part that is neither a lookup nor a trailing transform raises.

    ``year`` is a valid transform on a ``DateField``, but here ``day`` follows a
    scalar ``TextField`` where it resolves as neither a lookup nor a transform.
    """
    terminal = Book._meta.get_field("title")
    with pytest.raises(LookupValidationError) as excinfo:
        validate_lookup_expr(terminal, "day")

    assert excinfo.value.part == "day"


@pytest.mark.parametrize("lookup_expr", ["isnull", "exact", "in"])
def test_validate_lookup_expr_relation_descriptor_terminal(lookup_expr):
    """A relation-descriptor terminal resolves relation lookups (isnull/exact/in).

    A reverse-FK descriptor (``Book.loans`` -> ``ManyToOneRel``) answers
    ``get_lookup`` with the ``Related*`` lookup family.
    """
    terminal = Book._meta.get_field("loans")
    resolved = validate_lookup_expr(terminal, lookup_expr)
    assert resolved.__name__.startswith("Related")


def test_validate_lookup_expr_forward_m2m_terminal_isnull():
    """A forward M2M descriptor terminal resolves ``isnull`` to a lookup class."""
    terminal = Book._meta.get_field("genres")
    resolved = validate_lookup_expr(terminal, "isnull")
    assert resolved.__name__ == "IsNull"


def test_validate_lookup_expr_empty_expr_raises():
    """An empty lookup expression raises."""
    terminal = Book._meta.get_field("title")
    with pytest.raises(LookupValidationError) as excinfo:
        validate_lookup_expr(terminal, "")

    assert excinfo.value.lookup_expr == ""


def test_validate_lookup_expr_empty_part_raises():
    """A trailing ``__`` (empty part) raises."""
    terminal = Book._meta.get_field("title")
    with pytest.raises(LookupValidationError) as excinfo:
        validate_lookup_expr(terminal, "date__")

    assert excinfo.value.part == ""


def test_lookup_validation_error_is_configuration_family():
    """``LookupValidationError`` is catchable as ConfigurationError and the base."""
    err = LookupValidationError(Book._meta.get_field("title"), "x", "x")
    assert isinstance(err, ConfigurationError)
    assert isinstance(err, DjangoStrawberryFrameworkError)


def test_lookup_validation_error_labels_unnamed_terminal_by_type():
    """A terminal without a ``name`` falls back to its type name in the message."""
    err = LookupValidationError(object(), "x", "x")
    assert "object" in str(err)


# ---------------------------------------------------------------------------
# path_traverses_to_many: byte-identical compatibility with the legacy walk.
# ---------------------------------------------------------------------------


def _legacy_traverses_to_many(model, field_path):
    """The pre-refactor lenient walk, frozen here as the compatibility oracle.

    Copied verbatim from ``git show HEAD:.../utils/relations.py`` and used ONLY
    to prove the ``classify_path``-based reimplementation returns byte-identical
    booleans across the adversarial matrix below.
    """
    current = model
    for segment in field_path.split("__"):
        try:
            field = current._meta.get_field(segment)
        except FieldDoesNotExist:
            return False
        if not getattr(field, "is_relation", False):
            return False
        if is_many_side_relation_kind(relation_kind(field)):
            return True
        related = getattr(field, "related_model", None)
        if related is None:
            return False
        current = related
    return False


# Frozen expected answers empirically collected from the legacy implementation
# executed via ``git show HEAD:...`` in a scratch shell (see task report).
_TRAVERSES_MATRIX = [
    # valid to-one / scalar -> False
    (Book, "title", False),
    (Book, "shelf__branch__name", False),
    (Book, "shelf__pk", False),
    (Patron, "card__barcode", False),
    (Decision, "supersedes__supersedes__question", False),
    (Book, "shelf__code", False),
    (Genre, "name", False),
    (Branch, "city", False),
    (Book, "shelf__branch", False),
    (Book, "shelf", False),
    (Patron, "card", False),
    # valid to-many -> True
    (Book, "loans__note", True),
    (Book, "genres__name", True),
    (Genre, "books__title", True),
    (Branch, "tags__tag", True),
    (Loan, "book__loans__patron__email", True),
    (Decision, "superseded_by_set__question", True),
    (Branch, "shelves__code", True),
    (Book, "genres", True),
    (Book, "loans", True),
    (Book, "shelf__branch__shelves__code", True),
    # unresolvable head -> False
    (Branch, "does_not_exist", False),
    (Book, "nonexistent__name", False),
    # garbage tail after scalar -> False
    (Book, "shelf__nope", False),
    (Book, "title__nonsense", False),
    # forward GenericForeignKey -> False (related_model is None)
    (TaggedItem, "content_object", False),
    (TaggedItem, "content_object__x", False),
    # many-then-garbage -> True (legacy short-circuits at the many hop)
    (Book, "genres__nonexistent", True),
    (Book, "loans__nonexistent__x", True),
    (Book, "genres__name__icontains", True),
    (Loan, "book__genres__nonsense", True),
]


@pytest.mark.parametrize(("model", "path", "expected"), _TRAVERSES_MATRIX)
def test_path_traverses_to_many_matches_legacy(model, path, expected):
    """The reimplementation returns the frozen legacy answer for every path."""
    assert path_traverses_to_many(model, path) is expected
    # And it agrees with the legacy walk executed live in-process.
    assert path_traverses_to_many(model, path) is _legacy_traverses_to_many(model, path)


def test_path_traverses_to_many_many_then_garbage_uses_lenient_fallback():
    """A many-then-garbage path exercises the ``PathResolutionError`` fallback.

    ``classify_path`` raises on the garbage tail; the lenient fallback recovers
    the legacy ``True`` (the first hop is a forward M2M) instead of ``False``.
    """
    with pytest.raises(PathResolutionError):
        classify_path(Book, "genres__nonexistent")
    assert path_traverses_to_many(Book, "genres__nonexistent") is True


def test_lenient_fallback_all_to_one_relation_terminal_returns_false():
    """The lenient fallback's fully-walked-to-one exit returns ``False`` directly.

    ``path_traverses_to_many`` reaches the lenient loop's final ``return False``
    only in isolation: an all-to-one path ending on a relation
    (``shelf__branch``) is classified successfully by ``classify_path`` (so the
    public function never falls back), leaving this exit exercised by a direct
    call on the private helper.
    """
    from django_strawberry_framework.utils.relations import _lenient_traverses_to_many

    assert _lenient_traverses_to_many(Book, "shelf__branch") is False


def test_path_traverses_to_many_is_cached():
    """Repeated checks reuse the bounded metadata cache."""
    path_traverses_to_many.cache_clear()
    try:
        assert path_traverses_to_many(Branch, "shelves__code") is True
        assert path_traverses_to_many(Branch, "shelves__code") is True
        info = path_traverses_to_many.cache_info()
        assert info.misses == 1
        assert info.hits == 1
    finally:
        path_traverses_to_many.cache_clear()


def test_classify_path_cached_wrapper_shares_bounded_cache():
    """``_classify_path_cached`` caches the frozen plan keyed on model + path."""
    from django_strawberry_framework.utils.relations import _classify_path_cached

    _classify_path_cached.cache_clear()
    try:
        first = _classify_path_cached(Book, "genres__name")
        second = _classify_path_cached(Book, "genres__name")
        assert first is second
        info = _classify_path_cached.cache_info()
        assert info.misses == 1
        assert info.hits == 1
    finally:
        _classify_path_cached.cache_clear()


def test_classify_path_public_is_uncached_accepts_unhashable_model():
    """Public ``classify_path`` stays uncached so unhashable test doubles work.

    A ``SimpleNamespace`` model is unhashable (it defines ``__eq__``); the
    public entry point must not route through the ``lru_cache`` wrapper.
    """
    first = classify_path(Book, "title")
    second = classify_path(Book, "title")
    # Uncached: a fresh frozen plan each call (equal but distinct objects).
    assert first == second
    assert first is not second
