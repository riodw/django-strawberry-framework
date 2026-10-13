"""The write skeleton tells a failed step from a step whose product is a list.

``mutations/resolvers.py::run_write_pipeline_sync`` short-circuits to the error
envelope only for a ``StepFailure``, the tagged failure a ``decode_step`` /
``write_step`` returns. A decode product that is itself a list is a product, so it
reaches the write step and the success tail. No flavor's decode product is a list,
so the skeleton is driven directly, with injected steps, over a real bound create
mutation inside the managed write transaction a ``DjangoSchema`` execution opens.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from apps.products import models as product_models
from apps.products.services import seed_data
from django.db import transaction

from django_strawberry_framework import DjangoMutation, DjangoType, finalize_django_types
from django_strawberry_framework.mutations import resolvers
from django_strawberry_framework.mutations.resolvers import StepFailure
from django_strawberry_framework.utils.errors import field_error
from django_strawberry_framework.utils.write_transaction import managed_write_transaction
from tests._info import make_info

if TYPE_CHECKING:
    from collections.abc import Iterator

    from django.db import models


@pytest.fixture(autouse=True)
# basedpyright: requested for its side effect; pytest refuses a usefixtures mark on a fixture
def _isolate_registry(isolate_global_registry: None) -> Iterator[None]:  # pyright: ignore[reportUnusedParameter]
    """Declare this module's types and mutation over a cleared registry."""
    yield


@pytest.fixture
def create_item() -> type[DjangoMutation]:
    """A bound ``create`` mutation over ``Item`` with the allow-any permission opt-out."""

    class ItemType(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = []

    finalize_django_types()
    del ItemType
    return CreateItem


@pytest.mark.django_db
def test_list_decode_product_reaches_the_write_step(create_item: type[DjangoMutation]):
    """A decode step whose product is a list is a success, not an error envelope."""
    seed_data(1)
    row = product_models.Item.objects.order_by("pk").first()
    assert row is not None
    written: list[list[str]] = []

    def write_step(_instance: models.Model | None, decoded: list[str]) -> models.Model:
        written.append(decoded)
        return row

    with transaction.atomic(), managed_write_transaction("default"):
        result = resolvers.run_write_pipeline_sync(
            create_item,
            info=make_info(),
            data=None,
            id=None,
            decode_step=lambda _instance: ["product"],
            write_step=write_step,
        )

    assert written == [["product"]]
    assert result == resolvers.payload_cls_for(create_item)(result=row, errors=[])


@pytest.mark.django_db
def test_step_failure_short_circuits_to_the_error_envelope(create_item: type[DjangoMutation]):
    """A ``StepFailure`` from the decode step is the error envelope; the write never runs."""
    error = field_error("name", "Bad name.")
    written: list[object] = []

    def write_step(_instance: models.Model | None, decoded: object) -> models.Model:
        written.append(decoded)
        raise AssertionError("the write step ran after a failed decode")

    with transaction.atomic(), managed_write_transaction("default"):
        result = resolvers.run_write_pipeline_sync(
            create_item,
            info=make_info(),
            data=None,
            id=None,
            decode_step=lambda _instance: StepFailure([error]),
            write_step=write_step,
        )

    assert written == []
    assert result == resolvers.payload_cls_for(create_item)(result=None, errors=[error])
