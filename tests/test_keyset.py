"""Package-side keyset-cursor tests: codec, bounds, window shapes, lateral seek.

The live keyset acceptance surface runs in
``examples/fakeshop/test_query/test_keyset_api.py`` (round-trips, stability,
uniform value-position, permission-aware decode - the README live-HTTP-first
rule). These stay package-side because they assert what a live query cannot:
construction/finalization ``ConfigurationError`` branches, the codec's
rejection matrix (a live request only ever shows the uniform error), the
shared bounds contract's error arms, SQL shape of the two window renderings,
the lateral seek's raw-SQL forms plus its fetch-time structural recognition,
and the defensive fallback arms no planned query produces.
"""

import base64

import pytest
from apps.library.models import Book, Issue, Patron, Periodical
from apps.scalars.models import ScalarSpecimen
from django.test import override_settings
from graphql import GraphQLError
from strawberry.relay.utils import from_base64, to_base64

import django_strawberry_framework as framework
from django_strawberry_framework.exceptions import ConfigurationError, OptimizerError
from django_strawberry_framework.keyset import (
    _CURSOR_ENCRYPTION_CONTEXT,
    KEYSET_CURSOR_PREFIX,
    KeysetCursor,
    KeysetSeek,
    KeysetSeekPlan,
    _cursor_aessiv,
    _cursor_crypto_types,
    _decrypt_cursor_payload,
    _encrypt_cursor_payload,
    build_keyset_seek_plan,
    cursor_columns_for,
    decode_keyset_cursor,
    encode_keyset_cursor,
    keyset_seek_greater,
    keyset_seek_q,
    keyset_seek_sql,
    order_fingerprint,
    serialize_cursor_value,
    split_order_ref,
    validate_cursor_field_columns,
)
from django_strawberry_framework.utils.connections import (
    FetchMode,
    UnwindowableConnection,
    derive_keyset_window_bounds,
    resolve_relay_max_results,
    window_range_plan,
)
from tests._soft_dependency import simulated_absence

ISSUE_ORDER = ("-number", "id")


def _issue_columns():
    return cursor_columns_for(Issue, ISSUE_ORDER)


def _fingerprint():
    return order_fingerprint(ISSUE_ORDER)


def _mint(row, columns=None, fingerprint=None):
    return encode_keyset_cursor(
        columns or _issue_columns(),
        row,
        fingerprint=fingerprint or _fingerprint(),
    )


# ---------------------------------------------------------------------------
# split_order_ref / cursor_columns_for
# ---------------------------------------------------------------------------


def test_split_order_ref_parses_direction():
    assert split_order_ref("number") == ("number", False)
    assert split_order_ref("-number") == ("number", True)


def test_split_order_ref_rejects_bare_dash():
    with pytest.raises(ConfigurationError, match="Invalid cursor_field entry"):
        split_order_ref("-")


def test_split_order_ref_rejects_non_string_entry():
    with pytest.raises(ConfigurationError, match="must be a string"):
        split_order_ref(7)  # type: ignore[arg-type]


def test_cursor_columns_for_resolves_pk_alias():
    (column,) = cursor_columns_for(Issue, ("pk",))
    assert column.name == "pk"
    assert column.field is Issue._meta.pk
    assert column.value_source == "id"


# ---------------------------------------------------------------------------
# validate_cursor_field_columns (the finalization column contract)
# ---------------------------------------------------------------------------


def test_validate_cursor_field_accepts_declared_shape():
    validate_cursor_field_columns("IssueType", Issue, ("-number", "id"))
    validate_cursor_field_columns("IssueType", Issue, ("pk",))
    # A unique non-pk terminal also anchors a total order.
    validate_cursor_field_columns("PatronType", Patron, ("name",))


@pytest.mark.parametrize(
    ("cursor_field", "expected"),
    [
        (("--number", "id"), "not a valid order string"),
        (("periodical__name", "id"), "traverses a relation"),
        (("number", "-number", "id"), "more than once"),
        ((), "must contain at least one order string"),
    ],
)
def test_validate_cursor_field_references_match_declaration_rules(cursor_field, expected):
    """Finalization applies the same entry syntax and duplicate rules as class creation."""
    with pytest.raises(ConfigurationError, match=expected):
        validate_cursor_field_columns("IssueType", Issue, cursor_field)


def test_validate_cursor_field_rejects_unknown_column():
    with pytest.raises(ConfigurationError, match="does not resolve to a field"):
        validate_cursor_field_columns("IssueType", Issue, ("nope", "id"))


def test_validate_cursor_field_rejects_relation_column():
    with pytest.raises(ConfigurationError, match="local concrete column"):
        validate_cursor_field_columns("IssueType", Issue, ("periodical", "id"))


def test_validate_cursor_field_rejects_nullable_column():
    with pytest.raises(ConfigurationError, match="nullable"):
        validate_cursor_field_columns("BookType", Book, ("subtitle", "id"))


def test_validate_cursor_field_rejects_json_column():
    with pytest.raises(ConfigurationError, match="JSON ordering differs"):
        validate_cursor_field_columns("ScalarType", ScalarSpecimen, ("payload", "id"))


def test_validate_cursor_field_rejects_non_unique_terminal():
    with pytest.raises(ConfigurationError, match="must end in a unique column"):
        validate_cursor_field_columns("IssueType", Issue, ("number",))


# ---------------------------------------------------------------------------
# codec: round-trip + the rejection matrix
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_cursor_round_trip_preserves_values():
    periodical = Periodical.objects.create(name="P")
    issue = Issue.objects.create(periodical=periodical, number=7, title="seven")
    cursor = _mint(issue)
    decoded = decode_keyset_cursor(
        cursor,
        _issue_columns(),
        fingerprint=_fingerprint(),
        argument="after",
    )
    assert decoded.values == (7, issue.pk)


def test_cursor_payload_is_deterministic_and_confidential():
    sentinel = "cursor-secret-value"
    columns = cursor_columns_for(Patron, ("name",))
    row = Patron(name=sentinel)
    cursor = encode_keyset_cursor(
        columns,
        row,
        fingerprint=order_fingerprint(("name",)),
    )
    assert cursor == encode_keyset_cursor(
        columns,
        row,
        fingerprint=order_fingerprint(("name",)),
    )
    prefix, encrypted = from_base64(cursor)
    assert prefix == KEYSET_CURSOR_PREFIX
    assert sentinel not in encrypted
    assert sentinel.encode() not in base64.urlsafe_b64decode(encrypted)


def test_decrypt_cursor_payload_normalizes_token_and_json_errors():
    from django.conf import settings as django_settings

    with pytest.raises(GraphQLError, match="invalid cursor"):
        _decrypt_cursor_payload("\u00e9", "after")

    invalid_json = base64.urlsafe_b64encode(
        _cursor_aessiv(django_settings.SECRET_KEY).encrypt(
            b"not-json",
            [_CURSOR_ENCRYPTION_CONTEXT],
        ),
    ).decode()
    with pytest.raises(GraphQLError, match="invalid cursor"):
        _decrypt_cursor_payload(invalid_json, "after")


def test_cursor_crypto_is_cached_per_secret():
    _cursor_aessiv.cache_clear()
    first = _cursor_aessiv("cache-test-secret")
    assert _cursor_aessiv("cache-test-secret") is first
    assert _cursor_aessiv.cache_info().hits == 1


def test_cursor_crypto_cache_retains_every_rotation_key():
    """More than four configured secrets do not thrash the AES-SIV derivation cache."""
    secrets = tuple(f"rotation-secret-{index}" for index in range(6))
    _cursor_aessiv.cache_clear()
    first_pass = tuple(_cursor_aessiv(secret) for secret in secrets)
    second_pass = tuple(_cursor_aessiv(secret) for secret in secrets)
    assert second_pass == first_pass
    assert _cursor_aessiv.cache_info().hits == len(secrets)


def test_cursor_crypto_is_a_soft_dependency():
    with simulated_absence("cryptography", parent=framework, attr="keyset"):
        _cursor_aessiv.cache_clear()
        _cursor_crypto_types.cache_clear()
        with pytest.raises(ImportError, match="Meta.cursor_field requires cryptography"):
            _cursor_aessiv("missing-crypto-secret")
    _cursor_aessiv.cache_clear()
    _cursor_crypto_types.cache_clear()


def test_decode_rejects_non_base64():
    with pytest.raises(GraphQLError, match="invalid cursor"):
        decode_keyset_cursor(
            "!!not-base64!!",
            _issue_columns(),
            fingerprint=_fingerprint(),
            argument="after",
        )


def test_decode_rejects_foreign_prefix():
    with pytest.raises(GraphQLError, match="invalid cursor"):
        decode_keyset_cursor(
            to_base64("arrayconnection", 3),
            _issue_columns(),
            fingerprint=_fingerprint(),
            argument="after",
        )


@pytest.mark.django_db
def test_decode_rejects_tampered_ciphertext():
    periodical = Periodical.objects.create(name="P")
    issue = Issue.objects.create(periodical=periodical, number=1, title="one")
    cursor = _mint(issue)
    prefix, encrypted = from_base64(cursor)
    assert prefix == KEYSET_CURSOR_PREFIX
    tampered = to_base64(KEYSET_CURSOR_PREFIX, encrypted[:-2] + "xx")
    with pytest.raises(GraphQLError, match="invalid cursor"):
        decode_keyset_cursor(
            tampered,
            _issue_columns(),
            fingerprint=_fingerprint(),
            argument="after",
        )


@pytest.mark.django_db
def test_decode_rejects_fingerprint_mismatch():
    periodical = Periodical.objects.create(name="P")
    issue = Issue.objects.create(periodical=periodical, number=1, title="one")
    cursor = _mint(issue)
    with pytest.raises(GraphQLError, match="invalid cursor"):
        decode_keyset_cursor(
            cursor,
            _issue_columns(),
            fingerprint="title,id",
            argument="after",
        )


def _encrypted_payload_cursor(payload):
    return to_base64(KEYSET_CURSOR_PREFIX, _encrypt_cursor_payload(payload))


def test_decode_rejects_non_dict_payload():
    with pytest.raises(GraphQLError, match="invalid cursor"):
        decode_keyset_cursor(
            _encrypted_payload_cursor(["not", "a", "dict"]),
            _issue_columns(),
            fingerprint=_fingerprint(),
            argument="after",
        )


def test_decode_rejects_value_arity_mismatch():
    with pytest.raises(GraphQLError, match="invalid cursor"):
        decode_keyset_cursor(
            _encrypted_payload_cursor({"o": _fingerprint(), "v": ["1"]}),
            _issue_columns(),
            fingerprint=_fingerprint(),
            argument="after",
        )


def test_decode_rejects_non_list_values():
    with pytest.raises(GraphQLError, match="invalid cursor"):
        decode_keyset_cursor(
            _encrypted_payload_cursor({"o": _fingerprint(), "v": "12"}),
            _issue_columns(),
            fingerprint=_fingerprint(),
            argument="after",
        )


def test_decode_rejects_non_string_value_entries():
    with pytest.raises(GraphQLError, match="invalid cursor"):
        decode_keyset_cursor(
            _encrypted_payload_cursor({"o": _fingerprint(), "v": [1, 2]}),
            _issue_columns(),
            fingerprint=_fingerprint(),
            argument="after",
        )


def test_decode_rejects_unparsable_value_shape():
    with pytest.raises(GraphQLError, match="invalid cursor"):
        decode_keyset_cursor(
            _encrypted_payload_cursor({"o": _fingerprint(), "v": ["not-an-int", "2"]}),
            _issue_columns(),
            fingerprint=_fingerprint(),
            argument="after",
        )


@pytest.mark.django_db
def test_decode_honors_secret_key_fallbacks_rotation():
    """Key rotation keeps live cursors valid: old-key cursors verify via fallbacks."""
    from django.conf import settings as django_settings

    periodical = Periodical.objects.create(name="P")
    issue = Issue.objects.create(periodical=periodical, number=1, title="one")
    original_key = django_settings.SECRET_KEY
    cursor = _mint(issue)
    with override_settings(SECRET_KEY="rotated-new-key", SECRET_KEY_FALLBACKS=[original_key]):
        decoded = decode_keyset_cursor(
            cursor,
            _issue_columns(),
            fingerprint=_fingerprint(),
            argument="after",
        )
        assert decoded.values[0] == 1
    # Rotation WITHOUT the fallback rejects the old cursor (tamper-equivalent).
    with (
        override_settings(SECRET_KEY="rotated-new-key", SECRET_KEY_FALLBACKS=[]),
        pytest.raises(GraphQLError, match="invalid cursor"),
    ):
        decode_keyset_cursor(
            cursor,
            _issue_columns(),
            fingerprint=_fingerprint(),
            argument="after",
        )


def test_serialize_cursor_value_uses_field_codec():
    number_field = Issue._meta.get_field("number")
    assert serialize_cursor_value(number_field, 7) == "7"


def test_serialize_cursor_value_rejects_null():
    """NULL must not reach ``value_to_string`` (Char/Text would mint ``"None"``)."""
    title_field = Issue._meta.get_field("title")
    with pytest.raises(ValueError, match="NULL value for keyset cursor column"):
        serialize_cursor_value(title_field, None)
    number_field = Issue._meta.get_field("number")
    with pytest.raises(ValueError, match="NULL value for keyset cursor column"):
        serialize_cursor_value(number_field, None)


def test_encode_keyset_cursor_rejects_null_ordering_value():
    """Minting with a NULL column fails loudly instead of encoding string ``"None"``."""
    columns = cursor_columns_for(Issue, ("title", "id"))

    class _Shim:
        title = None
        id = 1

    with pytest.raises(GraphQLError, match="NULL value was read from 'title'"):
        encode_keyset_cursor(
            columns,
            _Shim(),
            fingerprint=order_fingerprint(("title", "id")),
        )


def test_encode_keyset_cursor_preserves_literal_string_none():
    """A real Char/Text value equal to ``\"None\"`` is still a valid cursor payload."""
    columns = cursor_columns_for(Issue, ("title", "id"))
    fingerprint = order_fingerprint(("title", "id"))

    class _Shim:
        title = "None"
        id = 1

    cursor = encode_keyset_cursor(columns, _Shim(), fingerprint=fingerprint)
    decoded = decode_keyset_cursor(
        cursor,
        columns,
        fingerprint=fingerprint,
        argument="after",
    )
    assert decoded.values == ("None", 1)


# ---------------------------------------------------------------------------
# seek predicate
# ---------------------------------------------------------------------------


def test_keyset_seek_greater_direction_table():
    """The canonical direction rule both seek dialects render from."""
    assert keyset_seek_greater(descending=False, flip=False) is True
    assert keyset_seek_greater(descending=True, flip=False) is False
    assert keyset_seek_greater(descending=False, flip=True) is False
    assert keyset_seek_greater(descending=True, flip=True) is True


def test_build_keyset_seek_plan_mixed_and_uniform():
    """The shared plan owns directions, values, and the uniform/lead facts."""
    mixed = build_keyset_seek_plan([True, False], (3, 1))
    assert mixed == KeysetSeekPlan(greater=(False, True), values=(3, 1))
    assert mixed.uniform is False
    assert mixed.lead_greater is False
    flipped = build_keyset_seek_plan([True, False], (3, 1), flip=True)
    assert flipped.greater == (True, False)
    assert flipped.lead_greater is True
    uniform = build_keyset_seek_plan([False, False], (3, 1))
    assert uniform.uniform is True
    assert uniform.lead_greater is True
    with pytest.raises(ValueError, match="at least one column"):
        KeysetSeekPlan(greater=(), values=())
    with pytest.raises(ValueError, match="arity mismatch"):
        build_keyset_seek_plan([False], (1, 2))


def test_keyset_seek_sql_uniform_row_value_and_mixed_or_expansion():
    """SQL renderer: row-value when uniform; leading-bound OR-expansion when mixed."""
    uniform = build_keyset_seek_plan([False, False], (3, 1))
    sql, params = keyset_seek_sql(['"number"', '"id"'], uniform)
    assert sql == '("number", "id") > (%s, %s)'
    assert params == [3, 1]
    single = build_keyset_seek_plan([False], (5,))
    sql, params = keyset_seek_sql(['"id"'], single)
    assert sql == '"id" > %s'
    assert params == [5]
    mixed = build_keyset_seek_plan([True, False], (3, 1))
    sql, params = keyset_seek_sql(['"number"', '"id"'], mixed)
    assert sql == ('"number" <= %s AND ("number" < %s OR ("number" = %s AND "id" > %s))')
    assert params == [
        3,
        3,
        3,
        1,
    ]
    with pytest.raises(ValueError, match="column refs"):
        keyset_seek_sql(['"number"'], mixed)


@pytest.mark.django_db
def test_keyset_seek_q_mixed_directions_both_ways():
    periodical = Periodical.objects.create(name="P")
    issues = [
        Issue.objects.create(periodical=periodical, number=number, title=str(number))
        for number in (1, 2, 3)
    ]
    columns = _issue_columns()
    cursor = KeysetCursor(values=(2, issues[1].pk))
    after = list(Issue.objects.filter(keyset_seek_q(columns, cursor)).order_by("-number", "id"))
    before = list(
        Issue.objects.filter(keyset_seek_q(columns, cursor, flip=True)).order_by("-number", "id"),
    )
    # Under (-number, id): "after" the cursor means SMALLER numbers.
    assert [issue.number for issue in after] == [1]
    assert [issue.number for issue in before] == [3]


@pytest.mark.django_db
def test_keyset_seek_carrier_q_matches_builder():
    columns = _issue_columns()
    cursor = KeysetCursor(values=(2, 1))
    seek = KeysetSeek(columns=columns, cursor=cursor)
    assert str(seek.q()) == str(keyset_seek_q(columns, cursor))
    assert seek.plan() == build_keyset_seek_plan(
        [column.descending for column in columns],
        cursor.values,
    )
    prepared = ("prep-3", "prep-1")
    assert seek.plan(prepared).values == prepared


# ---------------------------------------------------------------------------
# shared bounds contract
# ---------------------------------------------------------------------------


class _FakeConfig:
    relay_max_results = 50


class _FakeSchema:
    config = _FakeConfig()


class _FakeInfo:
    schema = _FakeSchema()


def test_derive_keyset_window_bounds_forward_shapes():
    bounds = derive_keyset_window_bounds(
        _FakeInfo(),
        before=None,
        after="x",
        first=3,
        last=None,
        max_results=None,
    )
    assert (bounds.offset, bounds.limit, bounds.reverse) == (0, 3, False)
    unbounded = derive_keyset_window_bounds(
        _FakeInfo(),
        before=None,
        after="x",
        first=None,
        last=None,
        max_results=None,
    )
    assert unbounded.limit == 50


def test_derive_keyset_window_bounds_backward_shapes_are_unwindowable():
    with pytest.raises(UnwindowableConnection):
        derive_keyset_window_bounds(
            _FakeInfo(),
            before="x",
            after=None,
            first=1,
            last=None,
            max_results=None,
        )
    with pytest.raises(UnwindowableConnection):
        derive_keyset_window_bounds(
            _FakeInfo(),
            before=None,
            after=None,
            first=None,
            last=2,
            max_results=None,
        )


def test_derive_keyset_window_bounds_first_validation():
    with pytest.raises(ValueError, match="non-negative"):
        derive_keyset_window_bounds(
            _FakeInfo(),
            before=None,
            after=None,
            first=-1,
            last=None,
            max_results=None,
        )
    with pytest.raises(ValueError, match="cannot be higher than 50"):
        derive_keyset_window_bounds(
            _FakeInfo(),
            before=None,
            after=None,
            first=51,
            last=None,
            max_results=None,
        )


def test_resolve_relay_max_results_precedence():
    assert resolve_relay_max_results(_FakeInfo(), 7) == 7
    assert resolve_relay_max_results(_FakeInfo(), None) == 50

    class _StrawberryWrapped:
        class schema:  # noqa: N801 - shape stub
            class _strawberry_schema:  # noqa: N801 - shape stub
                config = _FakeConfig()

    assert resolve_relay_max_results(_StrawberryWrapped(), None) == 50
    assert resolve_relay_max_results(object(), None) == 100


# ---------------------------------------------------------------------------
# window_range_plan keyset semantics
# ---------------------------------------------------------------------------


def test_window_range_plan_keyset_counted_floor_and_markers():
    plan = window_range_plan(offset=0, limit=2, reverse=False, keyset_counted=True)
    assert plan.lower_bound == 0  # the exclusive rn-0 floor
    assert plan.upper_bound == 2
    assert plan.add_marker_rows is True
    # The counted keyset seek fires only when totalCount is observed, so its
    # fetch mode is COUNTED (never PROBED - the seek count cannot come from a
    # probe); the probe is suppressed on the shape below.
    assert plan.fetch_mode(has_next_selected=True, total_selected=True) is FetchMode.COUNTED
    assert plan.next_page_probe is False


def test_window_range_plan_keyset_counted_suppresses_probe():
    plan = window_range_plan(
        offset=0,
        limit=2,
        reverse=False,
        next_page_probe=True,
        keyset_counted=True,
    )
    assert plan.next_page_probe is False


def test_window_range_plan_keyset_counted_unbounded_keeps_markers():
    plan = window_range_plan(offset=0, limit=None, reverse=False, keyset_counted=True)
    assert plan.lower_bound == 0
    assert plan.upper_bound is None
    assert plan.add_marker_rows is True


def test_window_range_plan_without_keyset_is_unchanged():
    plan = window_range_plan(offset=0, limit=2, reverse=False)
    assert plan.lower_bound is None
    assert plan.add_marker_rows is False


# ---------------------------------------------------------------------------
# apply_window_pagination keyset shapes (SQL rendering)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_apply_window_pagination_counted_keyset_serves_pre_seek_counts():
    """The counted seek window: page-relative rn, PRE-seek totals, abs-first markers."""
    from django_strawberry_framework.optimizer.plans import (
        WINDOW_KEYSET_SEEK_COUNT,
        WINDOW_ROW_NUMBER,
        WINDOW_ROW_NUMBER_ABS,
        WINDOW_TOTAL_COUNT,
        apply_window_pagination,
    )

    populated = Periodical.objects.create(name="populated")
    drained = Periodical.objects.create(name="drained")
    issues = [
        Issue.objects.create(periodical=populated, number=number, title=f"p{number}")
        for number in (
            1,
            2,
            3,
            4,
        )
    ]
    Issue.objects.create(periodical=drained, number=9, title="d9")
    # Cursor at p3 under (-number, id): "after" means numbers below 3.
    cursor = KeysetCursor(values=(3, issues[2].pk))
    seek = KeysetSeek(columns=_issue_columns(), cursor=cursor)
    windowed = apply_window_pagination(
        Issue.objects.all(),
        partition_by="periodical_id",
        order_by=ISSUE_ORDER,
        offset=0,
        limit=1,
        with_total_count=True,
        keyset_seek=seek,
    )
    rows = list(windowed.filter(periodical_id__in=[populated.pk, drained.pk]))
    by_partition = {}
    for row in rows:
        by_partition.setdefault(row.periodical_id, []).append(row)
    populated_rows = by_partition[populated.pk]
    # Page row: p2 with PAGE-RELATIVE rn 1; the qualify-wrapped filter kept the
    # partition count PRE-seek (4, not the 2 post-seek rows).
    page_row = next(r for r in populated_rows if getattr(r, WINDOW_ROW_NUMBER) == 1)
    assert page_row.title == "p2"
    assert getattr(page_row, WINDOW_TOTAL_COUNT) == 4
    assert getattr(page_row, WINDOW_KEYSET_SEEK_COUNT) == 2
    # The abs-first marker row (p4, rn 0 - before the seek) rides along.
    marker_row = next(r for r in populated_rows if getattr(r, WINDOW_ROW_NUMBER_ABS) == 1)
    assert marker_row.title == "p4"
    assert getattr(marker_row, WINDOW_ROW_NUMBER) == 0
    # The drained partition (its only row precedes the cursor... number 9 sorts
    # FIRST under -number, so it is pre-seek) keeps ONLY its marker, carrying
    # the true pre-seek count.
    drained_rows = by_partition[drained.pk]
    assert [getattr(r, WINDOW_ROW_NUMBER) for r in drained_rows] == [0]
    assert getattr(drained_rows[0], WINDOW_TOTAL_COUNT) == 1
    assert getattr(drained_rows[0], WINDOW_KEYSET_SEEK_COUNT) == 0


@pytest.mark.django_db
def test_apply_window_pagination_count_free_keyset_seeks_in_base_where():
    from django_strawberry_framework.optimizer.plans import apply_window_pagination

    seek = KeysetSeek(columns=_issue_columns(), cursor=KeysetCursor(values=(2, 1)))
    windowed = apply_window_pagination(
        Issue.objects.all(),
        partition_by="periodical_id",
        order_by=ISSUE_ORDER,
        offset=0,
        limit=2,
        with_total_count=False,
        next_page_probe=True,
        keyset_seek=seek,
    )
    sql = str(windowed.query)
    inner = sql.split('"qualify"')[0]
    assert "FILTER" not in sql
    assert '"number" <=' in inner  # the redundant leading bound, in the base WHERE
    # Probe overfetch: rn <= limit + 1.
    assert '"_dst_row_number" <= 3' in sql


def test_apply_window_pagination_rejects_reversed_keyset_seek():
    from django_strawberry_framework.optimizer.plans import apply_window_pagination

    seek = KeysetSeek(columns=_issue_columns(), cursor=KeysetCursor(values=(2, 1)))
    with pytest.raises(OptimizerError, match="cannot be reversed"):
        apply_window_pagination(
            Issue.objects.all(),
            partition_by="periodical_id",
            order_by=ISSUE_ORDER,
            limit=2,
            reverse=True,
            keyset_seek=seek,
        )


# ---------------------------------------------------------------------------
# lateral strategy: seek rendering + fetch-time recognition (SQLite-safe)
# ---------------------------------------------------------------------------


def _issue_lateral_request(seek, *, with_total_count=False, next_page_probe=False):
    from django_strawberry_framework.optimizer.join_taxonomy import classify_relation_join
    from django_strawberry_framework.optimizer.nested_fetch import NestedConnectionRequest

    field = Periodical._meta.get_field("issues")
    return NestedConnectionRequest(
        django_field=field,
        relation_field_name="issues",
        prefix="",
        child_queryset=Issue.objects.all(),
        join=classify_relation_join(field),
        order_by=ISSUE_ORDER,
        offset=0,
        limit=2,
        reverse=False,
        with_total_count=with_total_count,
        next_page_probe=next_page_probe,
        keyset_seek=seek,
        to_attr="_dst_issues_connection",
        lookup="issues",
    )


def _plan_lateral(request):
    from django_strawberry_framework.optimizer.lateral_fetch import LATERAL_STRATEGY
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    plan = OptimizationPlan()
    assert LATERAL_STRATEGY.plan(request, plan)
    return plan.prefetch_related[0].queryset


def _issue_seek(values=(3, 1), order=ISSUE_ORDER, flip=False):
    return KeysetSeek(
        columns=cursor_columns_for(Issue, order),
        cursor=KeysetCursor(values=values),
        flip=flip,
    )


def test_lateral_count_free_keyset_renders_in_branch_seek():
    from django_strawberry_framework.optimizer.lateral_fetch import (
        LateralQuerySet,
        build_lateral_sql,
    )

    seek = _issue_seek()
    lateral_queryset = _plan_lateral(_issue_lateral_request(seek, next_page_probe=True))
    assert isinstance(lateral_queryset, LateralQuerySet)
    spec = lateral_queryset._dst_lateral_spec
    assert spec.keyset_seek is seek
    sql, params = build_lateral_sql(spec, [1, 2], quote_name=lambda name: f'"{name}"')
    # Mixed directions (-number, id): redundant leading bound + OR expansion,
    # inside the branch, before the in-branch ORDER BY ... LIMIT.
    assert (
        '"library_issue"."number" <= %s AND ("library_issue"."number" < %s '
        'OR ("library_issue"."number" = %s AND "library_issue"."id" > %s))'
    ) in sql
    assert sql.index("LIMIT %s") > sql.index('"library_issue"."number" <=')
    assert params == [
        1,
        2,
        3,
        3,
        3,
        1,
        3,
    ]  # parents, seek values, page 2 + probe


def test_lateral_keyset_prepares_values_through_model_fields():
    from django_strawberry_framework.optimizer.lateral_fetch import build_lateral_sql

    spec = _plan_lateral(
        _issue_lateral_request(_issue_seek(), next_page_probe=True),
    )._dst_lateral_spec
    prepared = []

    def prepare_value(field, value):
        prepared.append((field.attname, value))
        return f"{field.attname}:{value}"

    _sql, params = build_lateral_sql(
        spec,
        [1],
        quote_name=lambda name: f'"{name}"',
        prepare_value=prepare_value,
    )
    assert prepared == [("periodical_id", 1), ("number", 3), ("id", 1)]
    assert params == [
        "periodical_id:1",
        "number:3",
        "number:3",
        "number:3",
        "id:1",
        3,
    ]


def test_lateral_uniform_keyset_renders_row_value_seek():
    from dataclasses import replace

    from django_strawberry_framework.optimizer.lateral_fetch import build_lateral_sql

    seek = _issue_seek(order=("number", "id"))
    request = replace(_issue_lateral_request(seek), order_by=("number", "id"))
    spec = _plan_lateral(request)._dst_lateral_spec
    sql, params = build_lateral_sql(spec, [1], quote_name=lambda name: f'"{name}"')
    assert '("library_issue"."number", "library_issue"."id") > (%s, %s)' in sql
    assert params == [
        1,
        3,
        1,
        2,
    ]


def test_lateral_single_column_keyset_renders_scalar_seek():
    from dataclasses import replace

    from django_strawberry_framework.optimizer.lateral_fetch import build_lateral_sql

    seek = _issue_seek(values=(5,), order=("pk",))
    request = replace(_issue_lateral_request(seek), order_by=("pk",))
    spec = _plan_lateral(request)._dst_lateral_spec
    sql, params = build_lateral_sql(spec, [1], quote_name=lambda name: f'"{name}"')
    assert '"library_issue"."id" > %s' in sql
    assert params == [1, 5, 2]


def test_lateral_counted_keyset_downgrades_to_windowed():
    from django_strawberry_framework.optimizer.lateral_fetch import LateralQuerySet

    windowed = _plan_lateral(_issue_lateral_request(_issue_seek(), with_total_count=True))
    assert not isinstance(windowed, LateralQuerySet)


def test_lateral_seek_arity_mismatch_downgrades_to_windowed():
    from django_strawberry_framework.optimizer.lateral_fetch import LateralQuerySet

    # One seek value, two order columns: the deterministic order grew a tail
    # the cursor does not carry.
    seek = KeysetSeek(
        columns=cursor_columns_for(Issue, ("pk",)),
        cursor=KeysetCursor(values=(5,)),
    )
    windowed = _plan_lateral(_issue_lateral_request(seek))
    assert not isinstance(windowed, LateralQuerySet)


def test_lateral_fetch_recognizes_planned_seek_residue():
    from django_strawberry_framework.optimizer.lateral_fetch import _recognize_lateral_fetch

    lateral_queryset = _plan_lateral(_issue_lateral_request(_issue_seek(), next_page_probe=True))
    spec = lateral_queryset._dst_lateral_spec
    filtered = lateral_queryset.filter(periodical__in=[1, 2])
    assert _recognize_lateral_fetch(filtered, spec).parent_ids == [1, 2]


def test_lateral_fetch_rejects_foreign_filters_and_missing_seek():
    from django_strawberry_framework.optimizer.lateral_fetch import _recognize_lateral_fetch

    lateral_queryset = _plan_lateral(_issue_lateral_request(_issue_seek(), next_page_probe=True))
    spec = lateral_queryset._dst_lateral_spec
    # A consumer filter beside the seek: never swallowed as the seek.
    poisoned = lateral_queryset.filter(periodical__in=[1]).filter(title__startswith="x")
    assert _recognize_lateral_fetch(poisoned, spec) is None
    # A seek-bearing spec over a body whose seek residue is ABSENT: mismatch.
    stripped = _plan_lateral(_issue_lateral_request(None, next_page_probe=True))
    assert _recognize_lateral_fetch(stripped.filter(periodical__in=[1]), spec) is None


def test_lateral_seek_quals_match_rejects_shape_drift():
    """The structural matcher's mismatch arms, driven directly."""
    from dataclasses import replace
    from types import SimpleNamespace

    from django_strawberry_framework.optimizer.lateral_fetch import (
        _is_window_qual,
        _keyset_seek_quals_match,
    )

    lateral_queryset = _plan_lateral(_issue_lateral_request(_issue_seek(), next_page_probe=True))
    spec = lateral_queryset._dst_lateral_spec
    seek_nodes = [
        child for child in lateral_queryset.query.where.children if not _is_window_qual(child)
    ]
    assert len(seek_nodes) == 2
    lead, expansion = seek_nodes
    assert _keyset_seek_quals_match([lead, expansion], spec)
    # Wrong count.
    assert not _keyset_seek_quals_match([lead], spec)
    # Swapped order (lead is not the comparison chain).
    assert not _keyset_seek_quals_match([expansion, lead], spec)
    # Wrong values: a seek for a DIFFERENT cursor.
    other_spec = replace(spec, keyset_seek=_issue_seek(values=(9, 9)))
    assert not _keyset_seek_quals_match([lead, expansion], other_spec)
    # A flipped-direction seek is not the planned one.
    flipped_spec = replace(spec, keyset_seek=_issue_seek(flip=True))
    assert not _keyset_seek_quals_match([lead, expansion], flipped_spec)

    # Missing/wrong-table lookup targets.
    targetless_lead = SimpleNamespace(
        lookup_name=lead.lookup_name,
        lhs=SimpleNamespace(target=None),
        rhs=lead.rhs,
    )
    assert not _keyset_seek_quals_match([targetless_lead, expansion], spec)
    foreign_target = SimpleNamespace(
        column=spec.order_columns[0][0],
        model=SimpleNamespace(_meta=SimpleNamespace(db_table="foreign_table")),
    )
    foreign_lead = SimpleNamespace(
        lookup_name=lead.lookup_name,
        lhs=SimpleNamespace(target=foreign_target),
        rhs=lead.rhs,
    )
    assert not _keyset_seek_quals_match([foreign_lead, expansion], spec)

    # Single-column cursors take the scalar expansion branch.
    single_seek = _issue_seek(values=(5,), order=("pk",))
    single_request = replace(_issue_lateral_request(single_seek), order_by=("pk",))
    single_queryset = _plan_lateral(single_request)
    single_spec = single_queryset._dst_lateral_spec
    single_nodes = [
        child for child in single_queryset.query.where.children if not _is_window_qual(child)
    ]
    assert _keyset_seek_quals_match(single_nodes, single_spec)

    arms = list(expansion.children)
    bad_lookup = SimpleNamespace(lookup_name="wrong")
    invalid_expansion = SimpleNamespace(children=None, negated=False, connector="OR")
    assert not _keyset_seek_quals_match([lead, invalid_expansion], spec)

    bad_first_arm = SimpleNamespace(
        children=[bad_lookup, arms[1]],
        negated=False,
        connector="OR",
    )
    assert not _keyset_seek_quals_match([lead, bad_first_arm], spec)

    malformed_second_arm = SimpleNamespace(children=None, negated=False, connector="AND")
    malformed_expansion = SimpleNamespace(
        children=[arms[0], malformed_second_arm],
        negated=False,
        connector="OR",
    )
    assert not _keyset_seek_quals_match([lead, malformed_expansion], spec)

    second_children = list(arms[1].children)
    bad_equal_arm = SimpleNamespace(
        children=[bad_lookup, second_children[1]],
        negated=False,
        connector="AND",
    )
    bad_equal_expansion = SimpleNamespace(
        children=[arms[0], bad_equal_arm],
        negated=False,
        connector="OR",
    )
    assert not _keyset_seek_quals_match([lead, bad_equal_expansion], spec)

    bad_cmp_arm = SimpleNamespace(
        children=[second_children[0], bad_lookup],
        negated=False,
        connector="AND",
    )
    bad_cmp_expansion = SimpleNamespace(
        children=[arms[0], bad_cmp_arm],
        negated=False,
        connector="OR",
    )
    assert not _keyset_seek_quals_match([lead, bad_cmp_expansion], spec)
