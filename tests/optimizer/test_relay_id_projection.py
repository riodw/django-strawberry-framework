"""Optimizer tests for Relay GlobalID projection when the pk attname is not ``id``.

The default-pk half is live at
``examples/fakeshop/test_query/test_products_visibility_api.py::test_relay_id_only_connection_page_costs_one_query_and_emits_decodable_ids``
and
``examples/fakeshop/test_query/test_products_visibility_api.py::test_relay_id_and_name_selection_is_clean_under_strictness_raise_over_http``.
The custom-attname half is carried by ``apps/library/models.py::PatronProfile``,
whose primary key is the one-to-one key to the patron it extends, so the column
an id projection must load is ``patron_id``.
"""

from types import SimpleNamespace

import pytest
import strawberry
from apps.library.models import Patron, PatronProfile
from strawberry import relay

from django_strawberry_framework import DjangoOptimizerExtension, DjangoType, finalize_django_types
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


@pytest.mark.django_db(transaction=True)
def test_relay_id_with_custom_pk_attname_avoids_lazy_load(django_assert_num_queries):
    """A Relay type whose pk attname is not ``id`` answers ``{ id postalCode }`` in one query.

    The walker resolves the configured ``id_attr``, projects the real pk column
    into ``only()``, and ``_resolve_id_default`` reads the loaded value from
    ``root.__dict__`` instead of falling back to ``getattr`` (spec-015 Decision
    7).
    """
    patron = Patron.objects.create(name="Ada")
    PatronProfile.objects.create(patron=patron, postal_code="EC1")

    class PatronType(DjangoType):
        class Meta:
            model = Patron
            fields = ("name",)

    class PatronProfileNode(DjangoType):
        class Meta:
            model = PatronProfile
            fields = ("patron", "postal_code")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query:
        @strawberry.field
        def all_profiles(self) -> list[PatronProfileNode]:
            return PatronProfile.objects.all()

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    with django_assert_num_queries(1):
        result = schema.execute_sync("{ allProfiles { id postalCode } }", context_value=ctx)

    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert "patron_id" in plan.only_fields
    assert "id" not in plan.only_fields
    assert result.data == {
        "allProfiles": [{"id": result.data["allProfiles"][0]["id"], "postalCode": "EC1"}],
    }
    node_id = relay.GlobalID.from_id(result.data["allProfiles"][0]["id"])
    assert node_id.type_name == PatronProfile._meta.label_lower
    assert node_id.node_id == str(patron.pk)
