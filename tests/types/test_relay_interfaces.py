"""Tests for the 0.0.5 Relay interfaces slice.

Covers ``Meta.interfaces`` validation, ``is_type_of`` injection, id
suppression, interface base-class injection, and the four Relay node
resolver defaults (``resolve_id_attr``, ``resolve_id``, ``resolve_node``,
``resolve_nodes``).
"""

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category, Item
from asgiref.sync import sync_to_async
from django.db.models import CompositePrimaryKey
from strawberry import relay

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.base import _build_annotations, _validate_interfaces
from django_strawberry_framework.types.definition import DjangoTypeDefinition
from django_strawberry_framework.types.relay import (
    _resolve_id_attr_default,
    _resolve_id_default,
    _resolve_node_default,
    _resolve_nodes_default,
    apply_interfaces,
    implements_relay_node,
    install_relay_node_resolvers,
)


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


def _meta(**attrs):
    """Build a throw-away ``Meta`` class with ``model=Category`` plus extras."""
    attrs.setdefault("model", Category)
    return type("Meta", (), attrs)


# ---------------------------------------------------------------------------
# Slice 1 — validation + storage
# ---------------------------------------------------------------------------


def test_meta_interfaces_accepted():
    """``interfaces = (relay.Node,)`` is normalized to ``(relay.Node,)``."""
    meta = _meta(interfaces=(relay.Node,))
    assert _validate_interfaces(meta) == (relay.Node,)


@pytest.mark.parametrize(
    "raw",
    [
        relay.Node,
        (relay.Node,),
        # Missing-comma spec spelling: Python evaluates ``(relay.Node)`` to
        # the bare class identity (not a tuple), so this case is identical
        # to the first; included verbatim per spec lines 192-193 / 323.
        (relay.Node),
    ],
)
def test_meta_interfaces_accepts_single_interface_class(raw):
    """A single class, a one-tuple, and the missing-comma spelling all normalize."""
    meta = _meta(interfaces=raw)
    assert _validate_interfaces(meta) == (relay.Node,)


@pytest.mark.parametrize(
    "raw",
    [
        {relay.Node},
        (x for x in (relay.Node,)),
        {relay.Node: None},
        42,
    ],
)
def test_meta_interfaces_rejects_non_sequence(raw):
    meta = _meta(interfaces=raw)
    with pytest.raises(ConfigurationError, match="must be a tuple/list"):
        _validate_interfaces(meta)


def test_meta_interfaces_rejects_string_entries():
    """Both top-level strings and tuple-of-string entries are rejected."""
    meta_top = _meta(interfaces="Node")
    with pytest.raises(ConfigurationError, match="must be a tuple/list"):
        _validate_interfaces(meta_top)
    meta_entry = _meta(interfaces=("Node",))
    with pytest.raises(ConfigurationError, match="must contain interface classes"):
        _validate_interfaces(meta_entry)


def test_meta_interfaces_rejects_non_interface_classes():
    """Plain classes, builtin types, and ``@strawberry.type``-decorated classes are rejected."""

    @strawberry.type
    class NotAnInterface:
        name: str

    for entry in (object, int, NotAnInterface):
        meta = _meta(interfaces=(entry,))
        with pytest.raises(ConfigurationError, match="not a Strawberry interface"):
            _validate_interfaces(meta)


@pytest.mark.parametrize(
    "entry",
    [
        object(),
        42,
    ],
)
def test_meta_interfaces_rejects_non_class_entries(entry):
    """Non-class non-string entries (instances, ints) raise the must-contain-interface-classes error."""
    meta = _meta(interfaces=(entry,))
    with pytest.raises(ConfigurationError, match="must contain interface classes"):
        _validate_interfaces(meta)


def test_meta_interfaces_rejects_djangotype_self_reference():
    """``DjangoType`` itself and any subclass are rejected as interface entries."""
    meta_self = _meta(interfaces=(DjangoType,))
    with pytest.raises(ConfigurationError, match="may not contain DjangoType"):
        _validate_interfaces(meta_self)

    class SomeType(DjangoType):
        pass

    meta_sub = _meta(interfaces=(SomeType,))
    with pytest.raises(ConfigurationError, match="may not contain DjangoType"):
        _validate_interfaces(meta_sub)


def test_meta_interfaces_rejects_duplicates():
    meta = _meta(interfaces=(relay.Node, relay.Node))
    with pytest.raises(ConfigurationError, match="duplicate entries"):
        _validate_interfaces(meta)


def test_meta_interfaces_empty_tuple_treated_as_unset():
    """An empty tuple and an absent key both produce ``()`` (bit-for-bit identical)."""
    assert _validate_interfaces(_meta(interfaces=())) == ()
    assert _validate_interfaces(_meta()) == ()


def test_meta_interfaces_stored_on_definition():
    """The normalized tuple flows through to ``DjangoTypeDefinition.interfaces``."""
    meta = _meta(interfaces=(relay.Node,))
    normalized = _validate_interfaces(meta)
    definition = DjangoTypeDefinition(
        origin=object,
        model=Category,
        name=None,
        description=None,
        fields_spec=None,
        exclude_spec=None,
        selected_fields=(),
        field_map={},
        optimizer_hints={},
        has_custom_get_queryset=False,
        interfaces=normalized,
    )
    assert definition.interfaces == (relay.Node,)


def test_meta_interfaces_end_to_end_accepted_in_validate_meta():
    """End-to-end ``class Meta: interfaces = (relay.Node,)`` flows through ``_validate_meta``.

    Slice 5 promoted ``"interfaces"`` from ``DEFERRED_META_KEYS`` to
    ``ALLOWED_META_KEYS``, so the deferred-key check no longer
    short-circuits the validator. This test pins that the full
    ``__init_subclass__`` path accepts the declaration and stores the
    normalized tuple on ``DjangoTypeDefinition``.
    """

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    assert CategoryNode.__django_strawberry_definition__.interfaces == (relay.Node,)


def test_class_already_inherits_relay_node_directly():
    """``_validate_interfaces`` accepts a Meta whose host class already inherits ``relay.Node``.

    Slice 1's contract is only that the validator accepts the tuple
    without raising. The structural no-op (skip bases already in
    ``cls.__mro__``) is Slice 4's job; this test deliberately does not
    inspect ``__bases__``.
    """

    class _Host(DjangoType, relay.Node):
        pass

    meta = _meta(interfaces=(relay.Node,))
    assert _validate_interfaces(meta) == (relay.Node,)
    # Reference _Host so ruff does not flag the host class as unused; the
    # class existing in the test module is the assertion shape per the plan.
    assert relay.Node in _Host.__mro__


def test_relay_node_with_composite_pk_raises(monkeypatch):
    """Composite-pk + ``relay.Node`` is rejected at finalization (Phase 2.5).

    The fakeshop apps do not ship a composite-pk model, so the test
    monkey-patches ``Category._meta.pk`` to a ``CompositePrimaryKey``
    instance for the duration of the test. Detection in Phase 2.5 is via
    ``isinstance(model._meta.pk, CompositePrimaryKey)`` per spec line 287.
    The error message names the model and proposes the two remediation
    paths (declare ``id: relay.NodeID[...]`` or remove ``relay.Node``).
    """

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    monkeypatch.setattr(Category._meta, "pk", CompositePrimaryKey("name", "is_private"))
    with pytest.raises(ConfigurationError, match="composite primary key"):
        finalize_django_types()


# ---------------------------------------------------------------------------
# Slice 2 — is_type_of injection
# ---------------------------------------------------------------------------


def test_is_type_of_injected_for_all_djangotypes():
    """``is_type_of`` is installed on every concrete ``DjangoType`` subclass.

    Decision 6 (spec line 351) is that injection is unconditional — it
    happens for every ``DjangoType`` subclass with a ``Meta`` regardless
    of whether ``Meta.interfaces`` is declared. The non-Relay
    ``DjangoType`` here exercises that unconditional path.

    The assertion uses ``cls.__dict__`` membership (not ``getattr``) so a
    method inherited from a base would not satisfy the contract; the
    injection must land on the class itself.
    """

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemNode(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    for type_cls, model_cls, other_model_cls in (
        (CategoryNode, Category, Item),
        (ItemNode, Item, Category),
    ):
        assert "is_type_of" in type_cls.__dict__
        is_type_of = type_cls.__dict__["is_type_of"]
        assert is_type_of(model_cls(), info=None) is True
        assert is_type_of(other_model_cls(), info=None) is False
        assert is_type_of(object(), info=None) is False


def test_consumer_declared_is_type_of_is_preserved():
    """A consumer-declared ``is_type_of`` on the class survives ``__init_subclass__``.

    Decision 6 (spec line 351): "If the consumer declares their own
    ``is_type_of``, we do not overwrite it." The discriminator is
    ``cls.__dict__`` membership, matching ``strawberry_django/type.py:204-211``.
    The sentinel return value proves the consumer's callable is the one
    that survives — not merely that some callable named ``is_type_of``
    is attached to the class.
    """
    sentinel = object()

    def consumer_is_type_of(obj, info):
        return sentinel

    class CustomNode(DjangoType):
        is_type_of = consumer_is_type_of

        class Meta:
            model = Category
            fields = ("id", "name")

    assert CustomNode.__dict__["is_type_of"] is consumer_is_type_of
    assert CustomNode.__dict__["is_type_of"](Category(), info=None) is sentinel


# ---------------------------------------------------------------------------
# Slice 3 — id suppression
# ---------------------------------------------------------------------------


def test_relay_node_strips_django_id_annotation():
    """``relay.Node`` in ``interfaces`` drops the synthesized pk annotation.

    Spec Decision 2 (lines 278-285): when ``relay.Node`` is declared the
    synthesized scalar ``id`` annotation must not shadow Strawberry's
    interface-supplied ``id: GlobalID!``. The field stays in ``fields`` so
    ``DjangoTypeDefinition.field_map`` and the optimizer still see the pk
    as a connector column (Decision 7, line 361).

    The unit-level test calls ``_build_annotations`` directly with a
    synthetic host class to keep the boundary tight. End-to-end
    coverage of the same suppression path lives in
    ``tests/types/test_definition_order_schema.py``.
    """
    fields = tuple(Category._meta.get_fields())

    class _Host:
        pass

    synthesized, _ = _build_annotations(
        _Host,
        fields,
        source_model=Category,
        interfaces=(relay.Node,),
    )
    assert "id" not in synthesized
    # Control: a non-pk scalar still receives its synthesized annotation so
    # the suppression is scoped to the primary key, not to all scalars.
    assert "name" in synthesized


def test_non_relay_type_keeps_id_int():
    """Without ``relay.Node`` declared, the synthesized ``id: int`` is preserved.

    Regression guard for the suppression branch: a future drift that
    accidentally strips ``id`` for non-Relay types must surface here. The
    ``interfaces=()`` default is the ``0.0.4``-identical path.
    """
    fields = tuple(Category._meta.get_fields())

    class _Host:
        pass

    synthesized, _ = _build_annotations(
        _Host,
        fields,
        source_model=Category,
        interfaces=(),
    )
    assert "id" in synthesized
    assert synthesized["id"] is int


# ---------------------------------------------------------------------------
# Slice 4 — interface base-class injection + Relay resolver defaults
# ---------------------------------------------------------------------------


def _build_fake_root(id_value: int):
    """Build a synthetic ``root`` whose ``__dict__`` is empty but ``getattr`` resolves the pk.

    Django model instances always cache the pk in ``__dict__`` when loaded
    through the ORM, so the literal "dict-cache miss" branch of
    ``_resolve_id_default`` is not reachable with a real saved row. The
    branch IS reachable when the root is a synthetic non-model object
    that mimics the ``__class__._meta.pk.attname`` contract — exactly the
    shape ``strawberry-django`` documents as the fallback path. We build
    that shape here so the fallback branch has a faithful test.
    """

    class _FakeRoot:
        pass

    # Mimic ``root.__class__._meta.pk.attname`` so the "pk" -> "id"
    # coercion in ``_resolve_id_default`` resolves cleanly.
    _FakeRoot._meta = Category._meta
    _FakeRoot.id = id_value
    return _FakeRoot()


def test_relay_node_injects_default_resolvers():
    """Phase 2.5 injects all four ``resolve_*`` classmethods onto a Relay-declared type."""

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    assert relay.Node in CategoryNode.__mro__
    for attr in ("resolve_id", "resolve_id_attr", "resolve_node", "resolve_nodes"):
        assert attr in CategoryNode.__dict__, f"{attr} was not injected"
        descriptor = CategoryNode.__dict__[attr]
        assert isinstance(descriptor, classmethod)


def test_resolve_id_attr_falls_back_to_pk():
    """No ``relay.NodeID[...]`` annotation -> ``resolve_id_attr()`` returns ``"pk"``."""

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    assert CategoryNode.resolve_id_attr() == "pk"
    # Direct helper exercise: the fallback fires when ``NodeIDAnnotationError`` raises.
    assert _resolve_id_attr_default(CategoryNode) == "pk"


@pytest.mark.django_db
def test_resolve_id_uses_dict_cache():
    """``resolve_id`` reads ``root.__dict__`` first (no extra lazy load)."""
    services.seed_data(1)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    row = Category.objects.only("id", "name").first()
    assert row is not None
    # Force a known pk into ``__dict__`` so the cache branch fires.
    row.__dict__["id"] = 9999
    assert CategoryNode.resolve_id(row, info=None) == "9999"


def test_resolve_id_falls_back_to_getattr():
    """When ``root.__dict__`` is missing the pk, ``resolve_id`` falls back to ``getattr``.

    Real Django model instances always cache the pk in ``__dict__``; the
    fallback branch only fires on synthetic ``root`` objects that mimic
    the ``__class__._meta.pk.attname`` contract. The synthetic shape is
    faithful to the spec contract at line 313 (``try ... __dict__ ...
    except KeyError: return str(getattr(root, id_attr))``).
    """

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    fake = _build_fake_root(42)
    assert "id" not in fake.__dict__
    assert CategoryNode.resolve_id(fake, info=None) == "42"


@pytest.mark.django_db
def test_resolve_node_applies_get_queryset():
    """A custom ``get_queryset`` filtering ``is_private`` scopes node lookup."""
    services.seed_data(1)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
            return queryset.filter(is_private=False)

    finalize_django_types()
    public_row = Category.objects.filter(is_private=False).first()
    private_row = Category.objects.filter(is_private=True).first()
    assert public_row is not None and private_row is not None
    assert CategoryNode.resolve_node(info=None, node_id=public_row.id).pk == public_row.pk
    assert CategoryNode.resolve_node(info=None, node_id=private_row.id) is None


@pytest.mark.django_db
def test_resolve_node_accepts_strawberry_positional_call_shape():
    """Strawberry calls ``cls.resolve_node(node_id, info=info)`` — positional ``node_id``.

    Pins the review-feedback regression (``feedback.md`` § High
    ``resolve_node`` default has the wrong bound signature): Strawberry's
    Relay machinery passes ``node_id`` positionally and ``info`` as a
    keyword. With the corrected signature ``(cls, node_id, *, info,
    required=False)`` this call shape lands correctly; with the previous
    ``(cls, info, node_id, ...)`` shape Python raised ``TypeError: got
    multiple values for argument 'info'``.
    """
    services.seed_data(1)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    target = Category.objects.first()
    assert target is not None
    # Positional node_id matches Strawberry's bound call site exactly.
    result = CategoryNode.resolve_node(str(target.pk), info=None)
    assert result is not None and result.pk == target.pk
    # required=True via positional node_id keeps the same shape.
    required_result = CategoryNode.resolve_node(str(target.pk), info=None, required=True)
    assert required_result.pk == target.pk


@pytest.mark.django_db
def test_resolve_node_required_raises_for_missing():
    """``required=True`` raises ``Model.DoesNotExist`` when no row matches."""
    services.seed_data(1)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    with pytest.raises(Category.DoesNotExist):
        CategoryNode.resolve_node(info=None, node_id=99999, required=True)


@pytest.mark.django_db
def test_resolve_nodes_preserves_order_and_missing():
    """``resolve_nodes(node_ids=[a, missing, b])`` returns ``[a, None, b]``."""
    services.seed_data(1)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    rows = list(Category.objects.order_by("id")[:2])
    a, b = rows[0], rows[1]
    results = CategoryNode.resolve_nodes(
        info=None,
        node_ids=[a.id, 999999, b.id],
        required=False,
    )
    assert results == [a, None, b]


@pytest.mark.django_db
def test_resolve_nodes_required_raises_for_missing():
    """``required=True`` raises ``Model.DoesNotExist`` for any missing id.

    Plural-path required-missing raises the model's ``DoesNotExist``, the
    same exception singular-path ``required=True`` raises via
    ``qs.get()``. This homogeneous shape lets consumers write one
    ``except Model.DoesNotExist:`` clause for both Relay node-lookup
    paths instead of two clauses (``DoesNotExist`` for singular,
    ``KeyError`` for plural).
    """
    services.seed_data(1)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    a = Category.objects.first()
    assert a is not None
    with pytest.raises(Category.DoesNotExist):
        CategoryNode.resolve_nodes(
            info=None,
            node_ids=[a.id, 999999],
            required=True,
        )


@pytest.mark.django_db
def test_resolve_nodes_without_ids_returns_full_queryset():
    """``node_ids=None`` returns the unfiltered queryset (caller materializes)."""
    services.seed_data(1)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    qs = CategoryNode.resolve_nodes(info=None)
    assert qs.model is Category
    assert qs.count() == Category.objects.count()


def _build_seeded_category_node():
    """Sync helper: seed catalog state, register a Relay-declared CategoryNode, finalize.

    Wrapped under ``sync_to_async(...)`` by the async tests below because
    ``services.seed_data``, ``DjangoType`` subclassing (which writes to
    the registry), and ``finalize_django_types`` are all sync paths that
    Django refuses to run inside an active event loop without explicit
    ``sync_to_async`` wrapping.
    """
    services.seed_data(1)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    return CategoryNode


@pytest.mark.django_db(transaction=True)
async def test_resolve_node_async_context():
    """In an async context ``_resolve_node_default`` awaits the matching row via ``afirst``."""
    CategoryNode = await sync_to_async(_build_seeded_category_node)()
    target = await Category.objects.afirst()
    assert target is not None

    result = await CategoryNode.resolve_node(info=None, node_id=target.id)
    assert result is not None
    assert result.pk == target.pk


@pytest.mark.django_db(transaction=True)
async def test_resolve_node_async_context_required():
    """In an async context ``_resolve_node_default(required=True)`` awaits via ``aget``."""
    CategoryNode = await sync_to_async(_build_seeded_category_node)()
    target = await Category.objects.afirst()
    assert target is not None

    result = await CategoryNode.resolve_node(info=None, node_id=target.id, required=True)
    assert result is not None
    assert result.pk == target.pk


@pytest.mark.django_db(transaction=True)
async def test_resolve_nodes_async_context():
    """Async ``_resolve_nodes_default`` preserves order and emits ``None`` for missing ids."""
    CategoryNode = await sync_to_async(_build_seeded_category_node)()
    rows = [row async for row in Category.objects.order_by("id")[:2]]
    a, b = rows[0], rows[1]

    result = await CategoryNode.resolve_nodes(
        info=None,
        node_ids=[a.id, 999999, b.id],
        required=False,
    )
    assert [obj.pk if obj is not None else None for obj in result] == [a.pk, None, b.pk]


@pytest.mark.django_db(transaction=True)
async def test_resolve_nodes_async_context_no_ids_returns_queryset():
    """``_resolve_nodes_default(node_ids=None)`` under async returns the lazy queryset.

    Async-branch contract (post-async-``get_queryset`` fix): the call
    returns a coroutine that yields the queryset once ``get_queryset``
    has been awaited. The caller awaits the resolver call to obtain the
    queryset, then iterates with ``async for``. Pins the spec line 491
    "node_ids=None" branch of Decision 9 under the corrected awaitable
    contract described in ``feedback.md`` § High.
    """
    CategoryNode = await sync_to_async(_build_seeded_category_node)()
    qs = await CategoryNode.resolve_nodes(info=None)
    assert qs.model is Category
    rows = [row async for row in qs]
    assert len(rows) == await Category.objects.acount()


def _build_seeded_category_node_with_async_get_queryset():
    """Sync helper: seed catalog state, register a Relay-declared ``CategoryNode`` with an async hook.

    The hook filters out ``is_private=True`` rows. Used by the async
    ``get_queryset`` tests below to prove that the async branch awaits
    the hook before applying the id filter.
    """
    services.seed_data(1)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        async def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
            return queryset.filter(is_private=False)

    finalize_django_types()
    return CategoryNode


@pytest.mark.django_db(transaction=True)
async def test_resolve_node_async_awaits_async_get_queryset():
    """Async ``get_queryset`` is awaited before the id filter on the async branch.

    Pins the review-feedback regression (``feedback.md`` § High): the
    previous implementation called ``cls.get_queryset(qs, info)``
    synchronously and then invoked ``.filter`` on the resulting
    coroutine, raising ``AttributeError``. The corrected async branch
    awaits the hook, then applies the id filter, then awaits
    ``aget``/``afirst``.
    """
    CategoryNode = await sync_to_async(_build_seeded_category_node_with_async_get_queryset)()
    public_row = await Category.objects.filter(is_private=False).afirst()
    private_row = await Category.objects.filter(is_private=True).afirst()
    assert public_row is not None and private_row is not None

    public_result = await CategoryNode.resolve_node(public_row.pk, info=None)
    assert public_result is not None and public_result.pk == public_row.pk
    # Rows the async hook filters out are invisible to the node lookup.
    assert await CategoryNode.resolve_node(private_row.pk, info=None) is None


@pytest.mark.django_db(transaction=True)
async def test_resolve_nodes_async_awaits_async_get_queryset():
    """Async ``get_queryset`` is awaited on the async ``resolve_nodes`` branch too.

    Mirrors ``test_resolve_node_async_awaits_async_get_queryset`` for
    the bulk-fetch path: the async branch awaits the hook before applying
    the ``id_attr__in`` filter, and the order-preserving missing-id
    contract still emits ``None`` at the indexes the hook filtered out.
    """
    CategoryNode = await sync_to_async(_build_seeded_category_node_with_async_get_queryset)()
    public_rows = [row async for row in Category.objects.filter(is_private=False).order_by("id")[:2]]
    private_row = await Category.objects.filter(is_private=True).afirst()
    assert len(public_rows) == 2 and private_row is not None
    a, b = public_rows

    result = await CategoryNode.resolve_nodes(
        info=None,
        node_ids=[a.pk, private_row.pk, b.pk],
        required=False,
    )
    # The private row is filtered out by the async hook, so its slot is None.
    assert [obj.pk if obj is not None else None for obj in result] == [a.pk, None, b.pk]


@pytest.mark.django_db(transaction=True)
async def test_resolve_nodes_async_no_ids_awaits_async_get_queryset():
    """Async ``resolve_nodes(node_ids=None)`` awaits the async hook and returns the filtered queryset.

    Pins the ``node_ids=None`` branch under async ``get_queryset``: the
    coroutine returned by ``resolve_nodes`` awaits the hook, applies no
    id filter, and yields the filtered queryset. Material rows reflect
    the hook's predicate.
    """
    CategoryNode = await sync_to_async(_build_seeded_category_node_with_async_get_queryset)()
    qs = await CategoryNode.resolve_nodes(info=None)
    rows = [row async for row in qs]
    # Every returned row must satisfy the async hook's predicate.
    assert rows
    assert all(row.is_private is False for row in rows)


def test_resolve_node_sync_with_async_get_queryset_raises():
    """Sync ``resolve_node`` + ``async def get_queryset`` raises ``ConfigurationError``.

    The sync branch cannot await an async hook; rather than letting
    ``.filter`` blow up on a coroutine, the framework closes the
    unawaited coroutine and raises a named ``ConfigurationError``
    pointing the consumer at the async resolver path or a sync hook
    rewrite (review feedback ``feedback.md`` § High).
    """

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        async def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
            return queryset

    finalize_django_types()
    with pytest.raises(ConfigurationError, match="returned a coroutine"):
        CategoryNode.resolve_node(1, info=None)


def test_resolve_nodes_sync_with_async_get_queryset_raises():
    """Sync ``resolve_nodes`` + ``async def get_queryset`` raises ``ConfigurationError``.

    Same contract as ``test_resolve_node_sync_with_async_get_queryset_raises``
    but for the bulk-fetch path. Both Relay node defaults must reject
    the sync-context + async-hook combination homogeneously so consumers
    see one error shape.
    """

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        async def get_queryset(cls, queryset, info, **kwargs):  # noqa: ARG003
            return queryset

    finalize_django_types()
    with pytest.raises(ConfigurationError, match="returned a coroutine"):
        CategoryNode.resolve_nodes(info=None)


async def test_consumer_async_resolve_node_wins():
    """An ``async def resolve_node`` on the consumer class survives injection."""
    sentinel = object()

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        async def resolve_node(cls, info, node_id, required=False):  # noqa: ARG003
            return sentinel

    finalize_django_types()

    assert await CategoryNode.resolve_node(info=None, node_id="anything") is sentinel


def test_consumer_resolve_id_attr_wins():
    """A consumer-declared ``resolve_id_attr`` survives Phase 2.5 injection."""

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        def resolve_id_attr(cls) -> str:
            return "name"

    finalize_django_types()
    assert CategoryNode.resolve_id_attr() == "name"


def test_consumer_resolve_id_wins():
    """A consumer-declared ``resolve_id`` survives Phase 2.5 injection."""
    sentinel_id = "consumer-id"

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        def resolve_id(cls, root, info) -> str:  # noqa: ARG003
            return sentinel_id

    finalize_django_types()
    assert CategoryNode.resolve_id(None, info=None) == sentinel_id


def test_consumer_resolve_node_wins():
    """A consumer-declared sync ``resolve_node`` survives Phase 2.5 injection."""
    sentinel = object()

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        def resolve_node(cls, info, node_id, required=False):  # noqa: ARG003
            return sentinel

    finalize_django_types()
    assert CategoryNode.resolve_node(info=None, node_id="x") is sentinel


def test_consumer_resolve_nodes_wins():
    """A consumer-declared ``resolve_nodes`` survives Phase 2.5 injection."""
    sentinel = [object()]

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        def resolve_nodes(cls, info, node_ids=None, required=False):  # noqa: ARG003
            return sentinel

    finalize_django_types()
    assert CategoryNode.resolve_nodes(info=None) is sentinel


def test_node_id_annotation_overrides_default_id_attr():
    """A ``relay.NodeID[str]`` annotation steers ``resolve_id_attr`` away from ``"pk"``.

    The consumer declares ``name: relay.NodeID[str]`` on the class (a
    column the model exposes). Strawberry's ``Node.resolve_id_attr()``
    walks ``cls.__annotations__`` for a ``relay.NodeID`` marker and
    returns that attribute's name; the ``NodeIDAnnotationError`` fallback
    never fires, so the framework default does not return ``"pk"``.

    The correct spelling is ``name: relay.NodeID[str]`` (a subscripted
    ``NodeID``); the bare ``Annotated[str, relay.NodeID]`` form does not
    register because Strawberry expects ``NodeIDPrivate`` instances in
    the metadata which only land via subscription.
    """

    class CategoryNode(DjangoType):
        name: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    assert CategoryNode.resolve_id_attr() == "name"


def test_non_relay_interface_works():
    """A non-Relay ``@strawberry.interface`` is injected without Relay resolver wiring."""

    @strawberry.interface
    class Auditable:
        name: str

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (Auditable,)

    finalize_django_types()
    assert Auditable in CategoryNode.__mro__
    # No Relay node injection on the consumer class.
    assert "resolve_node" not in CategoryNode.__dict__
    assert "resolve_id" not in CategoryNode.__dict__
    assert not implements_relay_node(CategoryNode)


def test_apply_interfaces_skips_already_present_bases():
    """``apply_interfaces`` is a no-op when the interface is already in ``__mro__``.

    Direct unit-boundary test against the ``apply_interfaces`` helper:
    constructs a host class whose MRO already contains ``relay.Node``,
    invokes the helper, and asserts ``__bases__`` is unchanged. Pins the
    structural-no-op contract from spec lines 329, 339, 458.
    """

    class _Host(DjangoType, relay.Node):
        pass

    original_bases = _Host.__bases__

    class _SyntheticDef:
        interfaces = (relay.Node,)

    apply_interfaces(_Host, _SyntheticDef)
    assert _Host.__bases__ == original_bases


def test_apply_interfaces_wraps_typeerror_as_configuration_error():
    """An incompatible base raises ``ConfigurationError`` with the interface named.

    A bare ``class _Host`` defaults to ``__bases__ == (object,)``. Appending a
    Strawberry interface produces ``(object, _BadInterface)``, which Python
    rejects with a "Cannot create a consistent MRO" ``TypeError`` because
    ``_BadInterface`` already inherits from ``object`` through a different
    metaclass path. The helper surfaces that as ``ConfigurationError`` naming
    the interface, per spec lines 540-541.
    """

    @strawberry.interface
    class _BadInterface:
        name: str

    class _Host:
        pass

    class _SyntheticDef:
        interfaces = (_BadInterface,)

    with pytest.raises(ConfigurationError, match="cannot add interface"):
        apply_interfaces(_Host, _SyntheticDef)


def test_resolve_id_default_unit_dict_cache_and_getattr_branches():
    """Direct unit-test of the dict-cache / ``getattr`` split (no DB hit)."""

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    # Dict-cache hit: explicitly seed ``__dict__``.
    inst = Category(id=7, name="x")
    inst.__dict__["id"] = 7
    assert _resolve_id_default(CategoryNode, inst, info=None) == "7"
    # Cache-miss fallback to ``getattr``: synthetic root whose ``__dict__``
    # is empty but whose class-level ``id`` attribute resolves the value.
    fake = _build_fake_root(12)
    assert _resolve_id_default(CategoryNode, fake, info=None) == "12"


@pytest.mark.django_db
def test_resolve_node_default_invoked_via_helper():
    """``_resolve_node_default`` works when invoked as a free function (not via classmethod)."""
    services.seed_data(1)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    target = Category.objects.first()
    assert target is not None
    result = _resolve_node_default(CategoryNode, info=None, node_id=target.id)
    assert result is not None and result.pk == target.pk


@pytest.mark.django_db
def test_resolve_nodes_default_invoked_via_helper():
    """``_resolve_nodes_default`` exercised as a free function with a ``relay.GlobalID``-coerced id."""
    services.seed_data(1)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    target = Category.objects.first()
    assert target is not None
    global_id = relay.GlobalID(type_name="CategoryNode", node_id=str(target.id))
    result = _resolve_nodes_default(
        CategoryNode,
        info=None,
        node_ids=[global_id],
        required=False,
    )
    assert len(result) == 1
    assert result[0] is not None and result[0].pk == target.pk


def test_install_relay_node_resolvers_idempotent():
    """Calling ``install_relay_node_resolvers`` twice yields the same ``__func__`` identity."""

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    snapshot = {
        attr: CategoryNode.__dict__[attr]
        for attr in (
            "resolve_id",
            "resolve_id_attr",
            "resolve_node",
            "resolve_nodes",
        )
    }
    install_relay_node_resolvers(CategoryNode)
    after = {attr: CategoryNode.__dict__[attr] for attr in snapshot}
    # After the first install the inherited defaults are framework defaults, so
    # the second install also writes framework defaults; identity should match
    # the first-pass snapshot because the underlying default callables are
    # module-level constants in ``types/relay.py``.
    for attr in snapshot:
        assert after[attr].__func__ is snapshot[attr].__func__


# ---------------------------------------------------------------------------
# Regression: direct ``relay.Node`` inheritance (no ``Meta.interfaces``)
# ---------------------------------------------------------------------------


def test_direct_relay_node_inheritance_suppresses_id_annotation():
    """Direct ``class Foo(DjangoType, relay.Node)`` suppresses the synthesized pk.

    Pins the review-feedback regression (``feedback.md`` § High "Direct
    ``relay.Node`` inheritance bypasses Relay finalization"): when a
    consumer follows Strawberry's native inheritance style without
    declaring ``Meta.interfaces``, the package must still drop the
    synthesized ``id: int`` annotation so the interface-supplied ``id:
    GlobalID!`` is not shadowed.

    Exercises ``_build_annotations`` at the unit boundary against a host
    class that itself inherits ``relay.Node``, with ``interfaces=()`` to
    isolate the direct-inheritance branch from the ``Meta.interfaces``
    branch.
    """
    fields = tuple(Category._meta.get_fields())

    class _Host(relay.Node):
        pass

    synthesized, _ = _build_annotations(
        _Host,
        fields,
        source_model=Category,
        interfaces=(),
    )
    assert "id" not in synthesized
    # Non-pk scalars still receive their synthesized annotations.
    assert "name" in synthesized


@pytest.mark.django_db
def test_direct_relay_node_inheritance_injects_resolvers_and_suppresses_id():
    """End-to-end: ``class Foo(DjangoType, relay.Node)`` finalizes the Relay shape.

    Pins the review-feedback regression (``feedback.md`` § High "Direct
    ``relay.Node`` inheritance bypasses Relay finalization"): Phase 2.5
    must run the composite-pk gate and the four ``resolve_*`` defaults
    for every class whose resolved MRO includes ``relay.Node``, not only
    for classes with a non-empty ``Meta.interfaces`` tuple. Without this
    fix the consumer's class still inherits ``relay.Node``'s defaults
    (which call into Strawberry's GlobalID encoder) but never receives
    the framework's ``get_queryset``-aware overrides.
    """
    services.seed_data(1)

    class CategoryNode(DjangoType, relay.Node):
        class Meta:
            model = Category
            fields = ("id", "name")

    finalize_django_types()
    assert relay.Node in CategoryNode.__mro__
    # ``Meta.interfaces`` was empty — the definition stores the empty tuple.
    assert CategoryNode.__django_strawberry_definition__.interfaces == ()
    # All four resolver defaults landed on the class itself.
    for attr in ("resolve_id", "resolve_id_attr", "resolve_node", "resolve_nodes"):
        assert attr in CategoryNode.__dict__, f"{attr} was not injected"
        assert isinstance(CategoryNode.__dict__[attr], classmethod)
    # The synthesized ``id`` annotation was dropped so the interface-supplied
    # ``id: GlobalID!`` field wins at Strawberry decoration time.
    assert "id" not in CategoryNode.__annotations__
    # Sanity: the injected defaults actually fetch by pk through ``get_queryset``.
    target = Category.objects.first()
    assert target is not None
    assert CategoryNode.resolve_node(str(target.pk), info=None).pk == target.pk


def test_direct_relay_node_inheritance_composite_pk_raises(monkeypatch):
    """Direct ``relay.Node`` inheritance + composite pk raises at finalization.

    Pins the review-feedback regression (``feedback.md`` § High): the
    composite-pk gate must fire for every Relay-shaped type, including
    consumers who inherit ``relay.Node`` directly without declaring
    ``Meta.interfaces``. Detection uses Phase 2.5's
    ``isinstance(model._meta.pk, CompositePrimaryKey)``.
    """

    class CategoryNode(DjangoType, relay.Node):
        class Meta:
            model = Category
            fields = ("id", "name")

    monkeypatch.setattr(Category._meta, "pk", CompositePrimaryKey("name", "is_private"))
    with pytest.raises(ConfigurationError, match="composite primary key"):
        finalize_django_types()


def test_install_relay_node_resolvers_preserves_consumer_override():
    """A consumer-declared ``resolve_id_attr`` is preserved by ``install_relay_node_resolvers``.

    Pin separately from the idempotency test: this one declares an
    explicit override on the class (its ``__func__`` differs from
    ``relay.Node.resolve_id_attr.__func__``) and asserts the helper does
    not overwrite it. Mirrors the ``test_consumer_resolve_id_attr_wins``
    end-to-end test but at the helper-boundary level so the override
    discriminator is exercised directly.
    """
    sentinel_value = "slug"

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        def resolve_id_attr(cls) -> str:
            return sentinel_value

    consumer_func = CategoryNode.__dict__["resolve_id_attr"].__func__
    # Manually drive the host class through Phase 2.5 without finalizing the
    # whole registry (the goal is to exercise the install helper directly).
    CategoryNode.__bases__ = (*CategoryNode.__bases__, relay.Node)
    install_relay_node_resolvers(CategoryNode)
    assert CategoryNode.__dict__["resolve_id_attr"].__func__ is consumer_func
    assert CategoryNode.resolve_id_attr() == sentinel_value
