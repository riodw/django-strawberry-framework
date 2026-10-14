"""Shared DjangoType/schema builders for strategy comparison harnesses.

Importable from both test tiers AND the benchmark scripts (the same
``pythonpath = examples/fakeshop`` / ``sys.path`` seam ``schema_reload.py``
uses), so the two-strategy schema construction the pg parity suite
(``tests/test_lateral_pg_parity.py``) and the nested-fetch benchmark
(``scripts/bench_nested_fetch.py``) compare against is ONE implementation -
a change to how a strategy is mounted on an extension then touches one
builder, not a test copy and a bench copy.

Nothing it imports needs ``django.setup()``: the bench bootstraps Django itself
after importing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry
from strawberry import relay

from django_strawberry_framework import DjangoOptimizerExtension, DjangoType, strawberry_config

if TYPE_CHECKING:
    from collections.abc import Mapping

    from django.db import models

    from django_strawberry_framework.optimizer.nested_fetch import StrategySelection


def make_django_type(
    name: str,
    model: type[models.Model],
    fields: tuple[str, ...],
    *,
    node: bool = True,
    meta_extra: Mapping[str, object] | None = None,
    namespace_extra: Mapping[str, object] | None = None,
) -> type[DjangoType]:
    """Declare a ``DjangoType`` over ``model`` (Relay-Node-shaped by default).

    The one ``type(name, (DjangoType,), {"Meta": ...})`` declaration core the
    ad-hoc type builders share; per-caller shorthands (a ``total_count``
    flag, a ``get_queryset`` hook) express themselves through ``meta_extra``
    / ``namespace_extra`` instead of re-spelling the core.
    """
    meta_attrs: dict[str, object] = {"model": model, "fields": fields}
    if node:
        meta_attrs["interfaces"] = (relay.Node,)
    if meta_extra:
        meta_attrs.update(meta_extra)
    namespace: dict[str, object] = {"Meta": type("Meta", (), meta_attrs)}
    if namespace_extra:
        namespace.update(namespace_extra)
    declared = type(name, (DjangoType,), namespace)
    assert issubclass(declared, DjangoType)
    return declared


def build_strategy_schema(
    query_cls: type[object],
    strategy: StrategySelection | None,
) -> strawberry.Schema:
    """One ``strawberry.Schema`` over ``query_cls`` running ``strategy``.

    ``strategy`` is a ``nested_connection_strategy`` selection (``"windowed"``,
    ``"lateral"``, an instance) mounted on ONE ``DjangoOptimizerExtension`` per
    built schema, wrapped in a factory so Strawberry's per-request
    ``get_extensions`` hands back that same instance every execution (the
    instance-bound plan cache survives); ``None`` builds the OPTIMIZER-OFF
    schema (the per-parent fallback pipeline the benchmark uses as its floor).
    """
    extensions = []
    if strategy is not None:
        optimizer = DjangoOptimizerExtension(nested_connection_strategy=strategy)
        extensions = [lambda: optimizer]
    return strawberry.Schema(
        query=query_cls,
        config=strawberry_config(),
        extensions=extensions,
    )
