"""Shared DjangoType/schema builders for strategy comparison harnesses.

Importable from both test tiers AND the benchmark scripts (the same
``pythonpath = examples/fakeshop`` / ``sys.path`` seam ``schema_reload.py``
uses), so the two-strategy schema construction the pg parity suite
(``tests/test_lateral_pg_parity.py``) and the nested-fetch benchmark
(``scripts/bench_nested_fetch.py``) compare against is ONE implementation -
a change to how a strategy is mounted on an extension then touches one
builder, not a test copy and a bench copy (docs/feedback.md DRY pass, T3).

Imports are function-local: the module must be importable before
``django.setup()`` (the bench bootstraps Django itself after importing).
"""

from __future__ import annotations

from typing import Any


def make_django_type(
    name: str,
    model: type,
    fields: tuple,
    *,
    node: bool = True,
    meta_extra: dict | None = None,
    namespace_extra: dict | None = None,
) -> type:
    """Declare a ``DjangoType`` over ``model`` (Relay-Node-shaped by default).

    The one ``type(name, (DjangoType,), {"Meta": ...})`` declaration core the
    ad-hoc type builders share; per-caller shorthands (a ``total_count``
    flag, a ``get_queryset`` hook) express themselves through ``meta_extra``
    / ``namespace_extra`` instead of re-spelling the core.
    """
    from django_strawberry_framework import DjangoType

    meta_attrs: dict[str, Any] = {"model": model, "fields": fields}
    if node:
        from strawberry import relay

        meta_attrs["interfaces"] = (relay.Node,)
    if meta_extra:
        meta_attrs.update(meta_extra)
    namespace: dict[str, Any] = {"Meta": type("Meta", (), meta_attrs)}
    if namespace_extra:
        namespace.update(namespace_extra)
    return type(name, (DjangoType,), namespace)


def build_strategy_schema(query_cls: type, strategy: Any) -> Any:
    """One ``strawberry.Schema`` over ``query_cls`` running ``strategy``.

    ``strategy`` is a ``nested_connection_strategy`` selection (``"windowed"``,
    ``"lateral"``, an instance) mounted on a fresh per-execution
    ``DjangoOptimizerExtension``; ``None`` builds the OPTIMIZER-OFF schema
    (the per-parent fallback pipeline the benchmark uses as its floor).
    """
    import strawberry

    from django_strawberry_framework import DjangoOptimizerExtension, strawberry_config

    extensions = []
    if strategy is not None:
        extensions = [lambda: DjangoOptimizerExtension(nested_connection_strategy=strategy)]
    return strawberry.Schema(
        query=query_cls,
        config=strawberry_config(),
        extensions=extensions,
    )
