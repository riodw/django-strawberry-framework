"""Tests for the shared query-source / visibility substrate (``utils/querysets.py``).

The 0.0.9 DRY pass (``docs/feedback.md`` Major 1) single-sited the query-source
contract the list field, connection field, optimizer middleware, Relay node
defaults, and filter related-visibility derive had each spelled separately:
``Manager`` -> ``QuerySet`` coercion, the is-queryset decision, and the sync /
async ``DjangoType.get_queryset`` visibility routing. ``get_queryset`` is the
visibility hook, so a divergence between those copies is a data-leak bug class;
these tests pin the neutral mechanics directly. The deep behavioral coverage
(through-schema list / connection / node / filter visibility) lives in the
surface suites (``tests/test_list_field.py``, ``tests/test_connection.py``,
``tests/test_relay_node_field.py``, ``tests/filters/test_sets.py``).
"""

from types import SimpleNamespace

import pytest
from apps.products.models import Category
from django.db import models

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.querysets import (
    SyncMisuseError,
    apply_type_visibility_async,
    apply_type_visibility_sync,
    initial_queryset,
    normalize_query_source,
    post_process_queryset_result_async,
    post_process_queryset_result_sync,
)


class _SyncType:
    """Duck-typed ``DjangoType`` stub with a sync ``get_queryset``."""

    __django_strawberry_definition__ = SimpleNamespace(model=Category)

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.exclude(name="__never__")


class _AsyncType:
    """Duck-typed ``DjangoType`` stub with an ``async def`` ``get_queryset``."""

    __django_strawberry_definition__ = SimpleNamespace(model=Category)

    @classmethod
    async def get_queryset(cls, queryset, info):
        return queryset


# ---------------------------------------------------------------------------
# normalize_query_source -- the single Manager-coercion / is-queryset decision
# ---------------------------------------------------------------------------


def test_normalize_query_source_coerces_manager_to_queryset():
    """A ``Manager`` becomes a ``QuerySet`` and reports ``is_queryset=True``."""
    source, is_queryset = normalize_query_source(Category.objects)
    assert isinstance(source, models.QuerySet)
    assert is_queryset is True


def test_normalize_query_source_passes_queryset_through():
    """A ``QuerySet`` passes through unchanged with ``is_queryset=True``."""
    qs = Category.objects.all()
    source, is_queryset = normalize_query_source(qs)
    assert source is qs
    assert is_queryset is True


def test_normalize_query_source_passes_non_queryset_through():
    """A non-queryset iterable passes through with ``is_queryset=False``."""
    payload = [1, 2, 3]
    source, is_queryset = normalize_query_source(payload)
    assert source is payload
    assert is_queryset is False


def test_initial_queryset_uses_default_manager():
    """``initial_queryset`` returns the declared model's ``_default_manager.all()``."""
    qs = initial_queryset(_SyncType)
    assert isinstance(qs, models.QuerySet)
    assert qs.model is Category


# ---------------------------------------------------------------------------
# apply_type_visibility_sync / _async -- the colored visibility routing
# ---------------------------------------------------------------------------


def test_apply_type_visibility_sync_runs_sync_get_queryset():
    """The sync path invokes ``get_queryset`` and returns its queryset."""
    base = Category.objects.all()
    result = apply_type_visibility_sync(_SyncType, base, info=None)
    assert isinstance(result, models.QuerySet)


def test_apply_type_visibility_sync_rejects_async_hook_loudly():
    """An ``async def`` ``get_queryset`` under the sync path raises ``SyncMisuseError``.

    The coroutine is closed before the raise (the ``filterwarnings = error``
    pytest config would fail the test on an unawaited-coroutine warning), and the
    typed marker is both a ``ConfigurationError`` and a ``RuntimeError``.
    """
    base = Category.objects.all()
    with pytest.raises(SyncMisuseError, match="returned a coroutine in a sync"):
        apply_type_visibility_sync(_AsyncType, base, info=None)
    assert issubclass(SyncMisuseError, ConfigurationError)
    assert issubclass(SyncMisuseError, RuntimeError)


async def test_apply_type_visibility_async_awaits_async_hook():
    """The async path awaits an ``async def`` ``get_queryset`` to a real queryset."""
    base = Category.objects.all()
    result = await apply_type_visibility_async(_AsyncType, base, info=None)
    assert isinstance(result, models.QuerySet)


async def test_apply_type_visibility_async_passes_sync_hook_through():
    """The async path passes a sync ``get_queryset`` return through without awaiting."""
    base = Category.objects.all()
    result = await apply_type_visibility_async(_SyncType, base, info=None)
    assert isinstance(result, models.QuerySet)


# ---------------------------------------------------------------------------
# post_process_queryset_result_* -- the list-field consumer-resolver shape
# ---------------------------------------------------------------------------


def test_post_process_sync_coerces_manager_then_applies_visibility():
    """A ``Manager`` return is coerced then run through ``get_queryset`` (sync)."""
    result = post_process_queryset_result_sync(_SyncType, Category.objects, info=None)
    assert isinstance(result, models.QuerySet)


def test_post_process_sync_passes_python_list_through():
    """A non-queryset Python list is returned unchanged (no visibility hook)."""
    payload = [object(), object()]
    result = post_process_queryset_result_sync(_SyncType, payload, info=None)
    assert result is payload


async def test_post_process_async_coerces_manager_then_applies_visibility():
    """A ``Manager`` return is coerced then awaited through ``get_queryset`` (async)."""
    result = await post_process_queryset_result_async(_AsyncType, Category.objects, info=None)
    assert isinstance(result, models.QuerySet)


async def test_post_process_async_passes_python_list_through():
    """A non-queryset Python list is returned unchanged on the async path."""
    payload = [object()]
    result = await post_process_queryset_result_async(_AsyncType, payload, info=None)
    assert result is payload
